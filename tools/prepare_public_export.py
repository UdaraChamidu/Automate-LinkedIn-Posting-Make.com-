"""Prepare an account-neutral public copy of a current Make export.

Usage: python tools/prepare_public_export.py "path/to/export.blueprint.json"
Reads the input without modifying it. Makes no network calls.
"""
from pathlib import Path
from copy import deepcopy
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['key','owner_chat_id','owner_user_id','publishing_enabled','draft_text',
          'draft_version','chat_history','image_prompt','image_file_id','image_version',
          'confirm_token','last_update_id','publish_lock','post_id','post_url','status',
          'visual_preferences','preview_message_id']

def walk(flow):
    for n in flow:
        yield n
        for route in n.get('routes',[]):
            yield from walk(route['flow'])
        yield from walk(n.get('onerror',[]))

def scrub(value):
    if isinstance(value,list):
        return [scrub(v) for v in value]
    if not isinstance(value,dict):
        return value
    result={}
    for k,v in value.items():
        if k in ('restore','setupValidation'):
            continue
        if k in ('__IMTCONN__','__IMTHOOK__'):
            result[k]=None
        elif k=='spreadsheetId' and isinstance(v,str) and '{{' not in v:
            result[k]='SET_GOOGLE_SPREADSHEET_ID'
        elif k=='label' and isinstance(v,str) and '@' in v:
            result[k]='Account'
        else:
            result[k]=scrub(v)
    return result

def prepare(source):
    raw=source.read_bytes()
    original=json.loads(raw.decode('utf-8-sig'))
    blueprint=deepcopy(original)
    nodes={n['id']:n for n in walk(blueprint['flow'])}
    expected={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,19}
    if set(nodes)!=expected:
        raise ValueError('This helper expects the documented 17-module workflow. Review another architecture separately.')
    if nodes[13]['module']!='telegram:DownloadFile' or nodes[14]['module']!='linkedin:ShareImage':
        raise ValueError('Unexpected media modules; do not apply field fixes blindly.')
    changes=[]
    if nodes[14]['mapper'].get('data')!='{{13.fileOutput}}':
        nodes[14]['mapper']['data']='{{13.fileOutput}}'
        changes.append('LinkedIn upload uses the actual Telegram fileOutput buffer.')
    nodes[14]['mapper']['fileName']='{{13.fileName}}'
    nodes[14]['filter']={'name':'Require downloaded image data','conditions':[[
        {'a':'{{13.fileOutput}}','o':'exist'}]]}
    changes.append('Image input filter checks existence of fileOutput; no buffer-to-text length assumption.')
    for group in nodes[6]['filter']['conditions']:
        action=next((c.get('b') for c in group if c.get('a')=='{{5.action}}'),None)
        for c in group:
            if c.get('a')=='{{length(5.reply)}}':
                c['b']='3500' if action=='chat' else '1200'
    editor=next(m for m in nodes[4]['mapper']['messages'] if m['role']=='system')
    editor['content']=editor['content'].replace(
        'Keep the reply within 900 characters. Present fewer findings if needed.',
        'Respect the action-specific reply limit. Present fewer findings if needed.')
    changes.append('Chat/draft/image reply caps are 3500/1200/1200; contradictory news-only 900 cap removed.')
    blueprint=scrub(blueprint)
    blueprint['name']='LinkedIn Content Automation - Public Template'
    blueprint['metadata']['designer']['orphans']=[]
    public_nodes={n['id']:n for n in walk(blueprint['flow'])}
    checks={}
    checks['17_unique_modules']=len(list(walk(blueprint['flow'])))==len(public_nodes)==17
    checks['research_precedes_editor']=any(
        [n['id'] for n in r['flow']][:3]==[19,4,5] for r in public_nodes[3]['routes'])
    checks['publishing_route_preserved']=any(
        [n['id'] for n in r['flow']]==[12,13,14,15,16] for r in public_nodes[3]['routes'])
    checks['connections_unbound']=all(
        all(v is None for k,v in n.get('parameters',{}).items() if k in ('__IMTCONN__','__IMTHOOK__'))
        for n in public_nodes.values())
    checks['file_output_mapped']=public_nodes[14]['mapper']['data']=='{{13.fileOutput}}'
    checks['file_output_filter']=public_nodes[14]['filter']['conditions'][0][0]['a']=='{{13.fileOutput}}'
    checks['parser_reads_editor']=public_nodes[5]['mapper']['json']=='{{get(4.choices; "1.message.content")}}'
    checks['sequential_processing']=blueprint['metadata']['scenario']['sequential'] is True
    text=json.dumps(blueprint,ensure_ascii=False,indent=2)+'\n'
    checks['no_obvious_tokens']=not bool(re.search(
        r'sk-[A-Za-z0-9_-]{15,}|\d{7,12}:[A-Za-z0-9_-]{25,}|Bearer\s+[A-Za-z0-9_-]{15,}',text))
    checks['no_email_addresses']=not bool(re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',text))
    # Known concrete source resources must be absent from the public copy.
    sheet=next(n for n in walk(original['flow']) if n['id']==2)['mapper']['spreadsheetId']
    checks['source_sheet_id_removed']=sheet not in text if '{{' not in sheet else True
    checks['no_hardcoded_owner_filter_ids']=all(
        not re.fullmatch(r'[+-]?\d{6,}',str(c.get('b','')))
        for n in public_nodes.values() for group in n.get('filter',{}).get('conditions',[])
        for c in group if 'chat.id' in c.get('a','') or 'from.id' in c.get('a',''))
    checks['legacy_image_data_path_removed']='13.data' not in text
    checks['source_untouched']=source.read_bytes()==raw
    if not all(checks.values()):
        raise ValueError('Public export checks failed: '+str([k for k,v in checks.items() if not v]))
    for folder in ('blueprints','prompts','docs','assets'):
        (ROOT/folder).mkdir(exist_ok=True)
    target=ROOT/'blueprints/LinkedIn_Content_Automation.blueprint.json'
    target.write_text(text,encoding='utf-8')
    (ROOT/'prompts/editor-system.txt').write_text(editor['content'].strip()+'\n',encoding='utf-8')
    (ROOT/'prompts/editor-user-template.txt').write_text(
        next(m['content'] for m in nodes[4]['mapper']['messages'] if m['role']=='user').strip()+'\n',encoding='utf-8')
    for name,field in [('research-instructions.txt','instructions'),('research-input-template.txt','input')]:
        (ROOT/'prompts'/name).write_text(nodes[19]['mapper'][field].strip()+'\n',encoding='utf-8')
    schema=['# State sheet','',
        'Create a native Google Sheet with one tab named **State**. Put these field names in row 1 and these initial values in row 2. Keep row 2 in place. This is one current-state record, not a post archive.','',
        '| Column | Row 1 heading | Initial row 2 value |','|---|---|---|']
    defaults={'key':'owner','owner_chat_id':'YOUR_TELEGRAM_CHAT_ID','owner_user_id':'YOUR_TELEGRAM_USER_ID',
              'publishing_enabled':'false','draft_version':'0','last_update_id':'0','status':'idle',
              'visual_preferences':'Professional uncluttered landscape illustration, no text or logos'}
    for i,f in enumerate(FIELDS):
        schema.append(f"| {chr(65+i)} | `{f}` | {defaults.get(f,'Leave blank')} |")
    schema+=['','Enter IDs and the lowercase publishing flag as plain text. Keep publishing disabled for initial checks. Do not put API keys in the sheet.','',
        'One new draft replaces the previous draft. To keep a publication archive, use a separate tab and an additional Add a Row step after confirmed publishing; it is not included in this template.','']
    (ROOT/'docs/state-sheet.md').write_text('\n'.join(schema),encoding='utf-8')
    audit={'scope':'Offline public-copy checks only. No live account access, API call, Make import or LinkedIn posting test.',
           'source_sha256':hashlib.sha256(raw).hexdigest(),'blueprint_sha256':hashlib.sha256(text.encode()).hexdigest(),
           'source_modified':False,'changes':changes,'checks':checks}
    (ROOT/'docs/export-validation.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print('Prepared public 17-module blueprint. '+str(len(checks))+' offline checks passed. Source unchanged.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    prepare(parser.parse_args().source)

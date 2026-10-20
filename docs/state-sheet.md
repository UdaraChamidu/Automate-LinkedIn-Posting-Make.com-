# State sheet

Create a native Google Sheet with one tab named **State**. Put these field names in row 1 and these initial values in row 2. Keep row 2 in place. This is one current-state record, not a post archive.

| Column | Row 1 heading | Initial row 2 value |
|---|---|---|
| A | `key` | owner |
| B | `owner_chat_id` | YOUR_TELEGRAM_CHAT_ID |
| C | `owner_user_id` | YOUR_TELEGRAM_USER_ID |
| D | `publishing_enabled` | false |
| E | `draft_text` | Leave blank |
| F | `draft_version` | 0 |
| G | `chat_history` | Leave blank |
| H | `image_prompt` | Leave blank |
| I | `image_file_id` | Leave blank |
| J | `image_version` | Leave blank |
| K | `confirm_token` | Leave blank |
| L | `last_update_id` | 0 |
| M | `publish_lock` | Leave blank |
| N | `post_id` | Leave blank |
| O | `post_url` | Leave blank |
| P | `status` | idle |
| Q | `visual_preferences` | Professional uncluttered landscape illustration, no text or logos |
| R | `preview_message_id` | Leave blank |

Enter IDs and the lowercase publishing flag as plain text. Keep publishing disabled for initial checks. Do not put API keys in the sheet.

One new draft replaces the previous draft. To keep a publication archive, use a separate tab and an additional Add a Row step after confirmed publishing; it is not included in this template.

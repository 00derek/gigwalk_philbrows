## Usage: 
- On slack, type `/update_geofence <project_id> <geofence_in_miles> <project_creator_email>`
- Sets the geofence (near_ticket_distance) of a project
- geofence is used by mobile clients to determine the maximum permissible distance from the
-   ticket location and where the photo answers can be submitted

## Technical details
Refer to slack_cmd_gwerinfo on how to build a Slack command, how to add a AWS API Gateway

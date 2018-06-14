
## Usage: 
on slack, type `/nudge PROJECT_ID CREATOR_EMAIL "YOUR MSG"` to comment/send Push notifications to all assiged Gigwalkers of assigned/started/scheduled tickets

## Lambda Env variable setup
- Now it's restricted to AUTHORIZED_USERS env variables and these are the handles on Slack
- It's also restricted to Slack team gigwalk
- Needs to make API/DB host as well as API token changes if we are testing against different env.

## Technical details
Now it's built with legacy customer integrations of slash command,
It could be even more complicated to build a Slack app:
https://api.slack.com/slack-apps#app_capabilities
if we need more capabilities.


### Slack slash command
- Go to [management dashbboard](https://gigwalk.slack.com/apps/A0F82E8CA-slash-commands?page=1) to create the custom command
- Define `command`, the name you want to expose to your user.
- Define `token`, this is needed for the security and used in the AWS lambda function later to verify the caller is from the internal.
- Define `URL`, this is the exposed AWS API gateway resource.
  e.g. `https://HOSTNAME.amazonaws.com/slackbot/whois`
- it will expect API response to return a JSON that could be rendered on slack, [basic formatting doc](https://api.slack.com/docs/message-formatting)
- [more slash command detailed documentation](https://api.slack.com/custom-integrations/slash-commands)

   
### AWS API Gateway
this is simply an API endpoint to proxy the request to the AWS lambda function for executing the tasks

- Create and Define `Slack-Bot` application
- Create stages: `slackbot`, which will expose an URL to you to use (basically you could create multiple stages to test out different versions and deployments)
- Under the application, create resource `/whois` and a method `POST`, you would select `Integration type` as `lambda function` or others, e.g. you just want to wrap an API, you would select `HTTP`
- then under API resources, you could `deploy the API` to the stage `slackbot` you just defined
- Go back to `POST -method execution`, since slack only using `application/x-www-form-urlencoded`, not `application/json` for the request body, we have to edit `POST - Integration Request` and add `Body Mapping Templates` as `application/x-www-form-urlencoded` and template as:
   
   ```
       ## convert HTTP POST data to JSON for insertion directly into a Lambda function
     
    ## first we we set up our variable that holds the tokenised key value pairs
    #set($httpPost = $input.path('$').split("&"))
     
    ## next we set up our loop inside the output structure
    {
    #foreach( $kvPair in $httpPost )
     ## now we tokenize each key/value pair using "="
     #set($kvTokenised = $kvPair.split("="))
     ## finally we output the JSON for this pair and add a "," if this isn't the last pair
     "$kvTokenised[0]" : "$kvTokenised[1]"#if( $foreach.hasNext ),#end
    #end
    }
   ```
### AWS lambda function
Implement the logic in `lambda_handler.handler` here, it could be running queries against DB, it could be executing a few BE APIs to complete a task, and etc. And it could be implemented with node.js or python or other languages, so most of the team members could do it effortlessly.
 - For this slack command, I simply query the Postgres and populate the response formatted with [Slack message formats](https://api.slack.com/docs/formatting/)
 - Logs are available through Cloudwatch, not very easy to debug but it's sufficient.
 - **Security note:** we should verify the caller and we should define sensitive information like DB hostname, DB name, and the credentials with the defined environment variables instead of embedding them in the code.
 - [more detailed AWS lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
 - Caveat: you have to wrap the libraries as modules and then you need to zip them together with your handler code to deploy.  See the repo for more details.
 - Caveat2: psycopg2 lib needs to be compiled within a Linux box or using the pre-compiled binary from https://github.com/jkehler/awslambda-psycopg2
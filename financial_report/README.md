
## Introduction:
- Return all public wf tickets executed in 3.0 since 2018-01-01

## Usage: 
- On slack, type `/report`, the access limited to Derek, Sriram and Bernice.
- It will return a S3 link contains the CSV file

## Lambda Env variable setup
- It's also restricted to Slack team gigwalk
- Needs to make API/DB host as well as API token changes if we are testing against different env.
- libraries required for this slack command to work are - https://s3.amazonaws.com/gigwalk-slack-command-libs/financil_report.zip


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
          ## convert HTML FORM POST data to JSON for insertion directly into a Lambda function
 
## get the raw post data from the AWS built-in variable and give it a nicer name
#set($rawPostData = $input.path('$'))
 
## first we get the number of "&" in the string, this tells us if there is more than one key value pair
#set($countAmpersands = $rawPostData.length() - $rawPostData.replace("&", "").length())
 
## if there are no "&" at all then we have only one key value pair.
## we append an ampersand to the string so that we can tokenise it the same way as multiple kv pairs.
## the "empty" kv pair to the right of the ampersand will be ignored anyway.
#if ($countAmpersands == 0)
 #set($rawPostData = $rawPostData + "&")
#end
 
## now we tokenise using the ampersand(s)
#set($tokenisedAmpersand = $rawPostData.split("&"))
 
## we set up a variable to hold the valid key value pairs
#set($tokenisedEquals = [])
 
## now we set up a loop to find the valid key value pairs, which must contain only one "="
#foreach( $kvPair in $tokenisedAmpersand )
 #set($countEquals = $kvPair.length() - $kvPair.replace("=", "").length())
 #if ($countEquals == 1)
  #set($kvTokenised = $kvPair.split("="))
  #if ($kvTokenised[0].length() > 0)
   ## we found a valid key value pair. add it to the list.
   #set($devNull = $tokenisedEquals.add($kvPair))
  #end
 #end
#end
 
## next we set up our loop inside the output structure "{" and "}"
{
#foreach( $kvPair in $tokenisedEquals )
  ## finally we output the JSON for this pair and append a comma if this isn't the last pair
  #set($kvTokenised = $kvPair.split("="))
 "$util.urlDecode($kvTokenised[0])" : #if(!$kvPair.endsWith("="))"$util.escapeJavaScript($util.urlDecode($kvTokenised[1]))"#{else}""#end#if( $foreach.hasNext ),#end
#end
}
   ```

### AWS lambda function
Implement the logic in `lambda_handler.handler` here, it could be running queries against DB, it could be executing a few BE APIs to complete a task, and etc. And it could be implemented with node.js or python or other languages, so most of the team members could do it effortlessly.
 - For this slack command, I simply query the Postgres and ouput it to S3, hence an IAM role to access S3 is needed
 - For security reason, the s3 bucket has defined a lifecycle which expires the file in a day-- check the defined bucket and its lifecycle definition.
 - Logs are available through Cloudwatch, not very easy to debug but it's sufficient.
 - **Security note:** we should verify the caller and we should define sensitive information like DB hostname, DB name, and the credentials with the defined environment variables instead of embedding them in the code.
 - [more detailed AWS lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
 - Caveat: you have to wrap the libraries as modules and then you need to zip them together with your handler code to deploy.  See the repo for more details.
 - Caveat2: psycopg2 lib needs to be compiled within a Linux box or using the pre-compiled binary from https://github.com/jkehler/awslambda-psycopg2

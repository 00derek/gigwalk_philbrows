
## Introduction:
- Resize the images taken by workers to thumbnails

## Usage: 
- For FE project summary page, for image stamped in data_items and located at 
http://[S3_BUCKET]/s3_file_key
e.g.
https://gigwalk-multitenant-api-server.s3.amazonaws.com/public_uploads/84adcb97964ad3778b6b159145de23ff4645a0a7b699a1b8018906da3bfe381c8c364e7d7d4cf1cf88184b345b3b8bedb00f670ec70ad52a0ac638eababddd10/5df86043-88ac-44b1-a2a8-523ec2172074

it will need to look for thumbnails at 
- http://[THUMBNAILS_HOST]/[ENV_NAME]/s3_file_key

- e.g. http://gigwalk-thumbnails.s3-website-us-east-1.amazonaws.com/multitenant/public_uploads/84adcb97964ad3778b6b159145de23ff4645a0a7b699a1b8018906da3bfe381c8c364e7d7d4cf1cf88184b345b3b8bedb00f670ec70ad52a0ac638eababddd10/5df86043-88ac-44b1-a2a8-523ec2172074

- For mobile, any new S3 images uploaded will be created in the same thumbnail bucket.


## Lambda Env variable setup
- No env variables are needed 
- libraries required for this slack command to work are - https://s3.amazonaws.com/gigwalk-slack-command-libs/image_resize.zip


## Technical details
- for older projects, since thumbnails are not existing, it implements [the design]
(https://aws.amazon.com/blogs/compute/resize-images-on-the-fly-with-amazon-s3-aws-lambda-and-amazon-api-gateway/)
Basically, if FE looking for thumbnails and it's not existing, it create the thumbnails on the fly and redirect it back to the user s.t. the later usage on the project summary will be able to use the thumbnails.  Note that the 1st call to the project summary is going to take some time.

- for newer projects, there are 3 s3 triggers existing for beta/staging/multitenant to create thumbnails when a photo being uploaded.  I didn't create it for 6 envs of CSMK/RSJP because these images will not be used until they deployed FE changes and if they do use FE.


   
### AWS API Gateway
 - as per the design, this is simply a GET endpoint redirected by S3 host s.t. it proxy the request to a lambda function to do the resize and later redirect the request to generated thumbnail image
 - it's defined in gw_hook/image-resize

### AWS lambda function
Implement the logic in `lambda_handler.handler` here, 
basically just take the original image in one s3 bucket and store the thumbnails to another s3 bucket

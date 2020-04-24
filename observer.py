import sys, time, logging, json
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, PatternMatchingEventHandler


"""
Events are: modified created, deleted moved

 - on_any_event: if defined, will be executed for any event
 - on_created: Executed when a file or a directory is created
 - on_modified: Executed when a file is modified or a directory renamed
 - on_moved: Executed when a file or directory is moved
 - on_deleted: Executed when a file or directory is deleted.
"""


class MyHandler(PatternMatchingEventHandler):
    patterns = ['*.xml', '*.csv'] #patterns attibute to watch

    def process(self, event):
        from datetime import datetime
        date_now = datetime.now()
        log_date = date_now.strftime('%d/%m/%Y %H:%M')
        print(log_date + ' - This '+event.src_path+' in '+event.event_type)

    
    def send_message_to_slack(self, text):
        from urllib import request, parse

        post = {"text": "{0}".format(text), "channel":"#basel-alertas"}

        try:
            json_data = json.dumps(post)
            req = request.Request("https://hooks.slack.com/services/<str>",
                                  data=json_data.encode('ascii'),
                                  headers={'Content-Type': 'application/json'}) 
            resp = request.urlopen(req)
        except Exception as em:
            print("EXCEPTION: " + str(em))

    def upload_to_s3_bucket(self, file_name, bucket, object_name=None):
        import boto3
        from botocore.exceptions import ClientError
        """
        Upload a file to an S3 bucket
         :param file_name: File to upload
         :param bucket: Bucket to upload to
         :param object_name: S3 object name. If not specified then file_name is used
         :return: True if file was uploaded, else False
        """

        if object_name is None: object_name = file_name

        s3_client = boto3.client('s3')
        try:
            #can use list to param 
            #upload_file([filename], [bucket], [key], callback=[...])
            response = s3_client.upload_file(file_name, bucket, object_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True


    def on_created(self, event):
        text = 'New file created in ' + event.src_path +' local path'
        self.send_message_to_slack(text)
        #self.upload_to_s3_bucket(file_name=event.src_path, bucket='bucket_name')
        self.process(event)


    def on_modified(self, event):
        text = 'File Modified ' + event.src_path +' local path'
        # self.send_message_to_slack(text)
        self.process(event)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
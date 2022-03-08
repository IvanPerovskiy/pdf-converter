import base64
import requests

url = 'http://ec2-3-135-63-195.us-east-2.compute.amazonaws.com/api/documents/'
headers = {
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjQzNzM5ODAxLCJpYXQiOjE2NDM3Mzk1MDEsImp0aSI6ImVjZWQyYTMwMzc4NDQ2NDViZDlmMjY4MjFlZjAyMmExIiwidXNlcl9pZCI6N30.MsvxVkdLRxllSZCflzXUAlL8fWNy40nERD5BeQQguGU'
}

load_path = './data/input'
input_path = '/'.join([load_path, 'ddd.docx'])
content = base64.b64encode(open(input_path, 'rb').read())
print(content)
data = {
            'name': 'new123.pdf',
            'body': content
        }
response = requests.post(url, data=data, headers=headers)
print(response.__dict__)
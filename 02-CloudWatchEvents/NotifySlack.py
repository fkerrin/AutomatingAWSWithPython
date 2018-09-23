import requests


url = ''  # Replace with slack webhook URL
data = {'text' : 'Testing slack notifications wwith iPython'}
requests.post(url, json = data)

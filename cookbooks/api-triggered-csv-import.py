import requests
import json

urlFile = "https://{{instance}}.quable.com/api/files"
urlImport = "https://{{instance}}.quable.com/api/imports"
headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer _MYAPITOKEN_'
}

# Push the local file
payload = {'fileType': 'import'}
files=[
  (
    'file',
    ('__FILENAME___',open('__PATH_TO_LOCAL_FILE__','rb'),'text/csv')
  )
]
responseFile = requests.request("POST", urlFile, headers=headers, data=payload, files=files, timeout=30)

# Retrieve the file ID that will be used when starting the import
fileId = responseFile['id']

# equivalent with CURL
# curl --location urlFile \
# --header 'Authorization: Bearer _MYAPITOKEN_' \
# --form 'file=@"__PATH_TO_LOCAL_FILE__"' \
# --form 'fileType="import"'

# Start the import
payloadImport = json.dumps({
    "importProfileId": "__IMPORT-PROFILE-ID__",
    "fileId": fileId
})
responseImport = requests.request("POST", urlImport, headers=headers, data=payloadImport, timeout=30)

from requests import post

data = {"data":[{"patient_id":"foo", "study_id":"study_id", "series_id":"series_id", "accession_number":"123", "series_number":"1"}],
        "dir":"foo"}


def run():
  print('running post')

  headers = {
    'content-type': 'application/json',
  }
  x  = post('http://localhost:5001/receive', json=data, headers=headers)
  print(x)

if __name__ == '__main__':
  run()
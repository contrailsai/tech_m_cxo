import requests 

def fetch(endpoint="/", method='get', body=''):
    url = f"http://localhost:8000{endpoint}"

    if method == 'get':
        try:
            response = requests.get(url, timeout=50)
            return response, response.json()
        except:
            raise "FAILED REQUEST"
        
    elif method =='post':
        try:
            response = requests.post(url, json=body, timeout=50)
            return response, response.json()
        except:
            raise "FAILED REQUEST"

    elif method =='put':
        try:
            response = requests.put(url, json=body, timeout=50)
            return response, response.json()
        except:
            raise "FAILED REQUEST"
        
    elif method =='delete':
        try:
            response = requests.delete(url, timeout=50)
            return response, response.json()
        except:
            raise "FAILED REQUEST"

if __name__ == "__main__":

    test_passed = 0
    try :
        # test-1: invalid url
        res, data = fetch('/docum')
        assert res.status_code == 404
        print("test-1 passed")
        test_passed +=1

        # test-2: fetch documents
        res, data = fetch('/documents')
        assert res.status_code == 200
        print("test-2 passed")
        test_passed +=1    

        _id = data[0]["_id"]

        # test-3: get a particular doc
        res, data = fetch(f'/document/{_id}')
        assert res.status_code == 200
        print("test-3 passed")
        test_passed +=1

        # test-4: invalid id for get doc 
        res, data = fetch(f'/document/98tjkdf')
        assert res.status_code == 400
        print("test-4 passed")
        test_passed +=1

        # test-5: non extsting id for get doc 
        res, data = fetch(f'/document/000000000000000000000000')
        assert res.status_code == 404
        print("test-5 passed")
        test_passed +=1

        # test-6: add doc (empty body)
        res, data = fetch(f'/add', method='post', body={})
        assert res.status_code == 400
        print("test-6 passed")
        test_passed +=1

        # test-7: Create a New Doc 
        dummy_data = {
            "name": "dummy_data",
            "text": "sample data"
        }
        res, data = fetch(f'/add', method='post', body=dummy_data)
        assert res.status_code == 201
        print("test-7 passed")
        test_passed +=1

        _id = data["id"]

        # test-8: update a Doc 
        res, data = fetch(f'/update/{_id}', method='put', body={"name": "updated dummpy data"})
        assert res.status_code == 201
        print("test-8 passed")
        test_passed +=1

        # test-9: Delete a Doc 
        res, data = fetch(f'/delete/{_id}', method='delete')
        assert res.status_code == 200
        print("test-9 passed")
        test_passed +=1

        # test-10: Delete a Doc invalid id 
        res, data = fetch(f'/delete/{666666}', method='delete')
        assert res.status_code == 400
        print("test-10 passed")
        test_passed +=1


        # CRAWL TEST

        # test-11: Crawl a site with invalid Link  
        res, data = fetch(f'/crawl', method='post', body={"link": "h://xtline"})
        assert res.status_code == 400
        print("test-11 passed")
        test_passed +=1

        # test-12: Crawl a site no link provided  
        res, data = fetch(f'/crawl', method='post', body={})
        assert res.status_code == 400
        print("test-12 passed")
        test_passed +=1

        # test-13: Crawl a site with LINKS  
        res, data = fetch(f'/crawl', method='post', body={"link": "https://xtradgpt.online"})
        assert res.status_code == 201
        print(data)
        assert data['success']
        assert data['video_count'] == 1
        print("test-13 passed")
        test_passed +=1

        _id = data['media_mongo_ids'][0]

        # processing test

        # test-14: Send to SQS no poi provided  
        res, data = fetch(f'/process-pending', method='post', body={"media_ids": [_id]})
        assert res.status_code == 400
        print("test-14 passed")
        test_passed +=1

        # test-15: Send to SQS   
        res, data = fetch(f'/process-pending', method='post', body={"media_ids": [_id], "poi_id": "00_POI_ID_00"})
        assert res.status_code == 201
        print("test-15 passed")
        test_passed +=1

    except :
        print("error occured at test", test_passed+1)
    finally:
        print("Test Passed :", test_passed)


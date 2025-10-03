import json
import requests
from urllib import request
from urllib.error import URLError, HTTPError
from file_util import find_new_file_name
import time
from random import randint

class Comfy():
    def __init__(self, workflow_path, api_url):
        self.workflow_path=workflow_path
        self.workflow=None
        self.api_url=api_url

    '''
    Saves .json workflow file to a instance attribute self.workflow
    '''
    def load_workflow(self):
        try:
            with open(f'{self.workflow_path}', 'r') as file:
                workflow=json.load(file)

            self.workflow=workflow
        
        except Exception as e:
            print(f"Error loading workflow file: {e}")

    def queue_prompt(self):
        try:
            p = {"prompt": self.workflow}
            data = json.dumps(p).encode('utf-8')
            
            req = request.Request(
                f"{self.api_url}/prompt", 
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with request.urlopen(req) as response:
                result = response.read().decode('utf-8')
                return json.loads(result)
                
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            print(f"Failed to queue prompt: {e}")
            return None

    def fetch_image(self, response, prompt_id):
        result = response[prompt_id]["outputs"]
        for node_id, node_output in result.items():
            if "images" in node_output:
                for img in node_output["images"]:
                    filename = img["filename"]
                    subfolder = img["subfolder"]
                    image_resp = requests.get(f"{self.api_url}/view?filename={filename}&subfolder={subfolder}&type=output")
                    new_filename = find_new_file_name(f'images/{filename}')

                    with open(f"{new_filename}.png", "wb") as f:
                        f.write(image_resp.content)
                    print(f"Saved {new_filename}")

    def get_image(self, pos_prompt, neg_prompt):

        if not self.workflow:
            self.load_workflow()

        # Insert positive and negative prompts into the loaded workflow
        self.workflow["6"]["inputs"]["text"] = pos_prompt
        self.workflow["7"]["inputs"]["text"] = neg_prompt
        self.workflow["3"]["inputs"]["seed"] = randint(1,9999999)  # Random seed

        prompt_id_json = self.queue_prompt()
        prompt_id=prompt_id_json["prompt_id"]
        print(f"Prompt in queue: ID: {prompt_id}")
        time.sleep(10)
        while True:
            response = requests.get(f"{self.api_url}/history/{prompt_id}")  # Check if image is generated
            if response.status_code == 200:  
                data = response.json()
                print(data)
                if prompt_id in data:
                    print("Result ready!") # If image is ready
                    self.fetch_image(data, prompt_id)
                break
            time.sleep(1)




# For testing purposes
'''
def main():
    comfy = Comfy("sdxl_turbo_workflow.json","http://127.0.0.1:8188")
    comfy.get_image("photo of a woman, ultrarealistic", "lowres, low quality")

if __name__ == "__main__":
    main()
'''
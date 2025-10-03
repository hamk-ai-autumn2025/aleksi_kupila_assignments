import json, copy
import requests
from urllib.error import URLError, HTTPError
from file_util import find_new_file_name
import time
from random import randint

class Comfy():
    def __init__(self, workflow_path, api_url, pos_node_id, neg_node_id, seed_node_id):
        self.workflow_path = workflow_path
        self.workflow = None
        self.api_url = api_url
        self.pos_node_id = pos_node_id
        self.neg_node_id = neg_node_id
        self.seed_node_id = seed_node_id

        self.load_workflow()

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

    def queue_prompt(self, workflow):
        try:
            p = {"prompt": workflow}
            data = json.dumps(p).encode('utf-8')
            
            response = requests.post(
                f"{self.api_url}/prompt", 
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            print(response)
            return response.json()
                
        except Exception as e:
            print(f"Failed to queue prompt: {e}")
            return None

    def fetch_image(self, response, prompt_id):

        for node_id, node_output in response.items():
            if "images" in node_output:
                for img in node_output["images"]:
                    filename = img["filename"]
                    subfolder = img["subfolder"]

                    try:
                        image_resp = requests.get(f"{self.api_url}/view?filename={filename}&subfolder={subfolder}&type=output", timeout=5)
                        new_filename = find_new_file_name(f'images/{filename}')

                        with open(f"{new_filename}", "wb") as f:
                            f.write(image_resp.content)
                        print(f"Saved {new_filename}")
                        return new_filename
                    except Exception as e:
                        print(f"Failed to fetch image: {e}")
                        return None

    def poll_for_result(self, prompt_id, timeout=20, interval=0.5):
        start = time.time()

        while True:
            try:
                response = requests.get(f"{self.api_url}/history/{prompt_id}", timeout=5)
                response.raise_for_status()
                data = response.json()

                if prompt_id in data and "outputs" in data[prompt_id]:
                    return data[prompt_id]["outputs"]
                
            except requests.RequestException:
                pass  # network error, try again

            if time.time() - start > timeout:
                raise TimeoutError(f"Prompt {prompt_id} not ready after {timeout} seconds.")
            
            time.sleep(interval)

    def get_image(self, pos_prompt, neg_prompt):

        workflow = copy.deepcopy(self.workflow)

        # Insert positive and negative prompts into the loaded workflow
        workflow[f"{self.pos_node_id}"]["inputs"]["text"] = pos_prompt
        workflow[f"{self.neg_node_id}"]["inputs"]["text"] = neg_prompt
        workflow[f"{self.seed_node_id}"]["inputs"]["noise_seed"] = randint(1,9999999)  # Random seed

        # Queue prompt, get prompt request ID
        prompt_id_json = self.queue_prompt(workflow)
        # Extract prompt id STR from the dict
        try:
            prompt_id=prompt_id_json["prompt_id"]
        except Exception as e:
            print(f"Error fetching prompt id: {e}")
        
        if prompt_id:
            print(f"Prompt in queue: ID: {prompt_id}")

            result = self.poll_for_result(prompt_id)
            img = self.fetch_image(result, prompt_id)
            return img
                        
        else: 
            return None




# For testing purposes

def main():
    comfy = Comfy("sdxlturbo_example.json","http://127.0.0.1:8188",6,7,13)
    comfy.get_image("ultrarealistic, best quality photo of a woman with brown hair, indoor setting, natural lighting", "lowres, disfigured, error, mistake, missing limbs, low quality")

if __name__ == "__main__":
    main()

from pathlib import Path
import json, copy
import requests
from urllib.error import URLError, HTTPError
from .file_util import find_new_file_name
import time
from random import randint

class Comfy():
    """
    A client for integrating with ComfyUI API to generate images.
    
    This class provides a simple interface to queue image generation prompts,
    poll for completion, and fetch the resulting images from a ComfyUI instance.
    
    Attributes:
        workflow_path (str): Path to the workflow JSON file
        workflow (dict): Loaded workflow configuration
        api_url (str): Base URL for the ComfyUI API
        pos_node_id (str): Node ID for positive prompt in workflow
        neg_node_id (str): Node ID for negative prompt in workflow
        seed_node_id (str): Node ID for seed parameter in workflow
    """
    
    def __init__(self, workflow_path: str = "/workflows/sdxlturbo_example.json", api_url: str = "http://127.0.0.1:8188", pos_node_id: str = "6", neg_node_id: str = "7", resolution_id: str = "5", seed_node_id: str = "13", base_dir: str = None):
        """
        Initialize the Comfy API client.
        
        Args:
            workflow_path (str): Path to the API-compatible workflow JSON file
            api_url (str): Base URL of the ComfyUI API endpoint
            pos_node_id (str): Node ID for positive prompt in the workflow
            neg_node_id (str): Node ID for negative prompt in the workflow
            seed_node_id (str): Node ID for seed parameter in the workflow
        """

        # Directory where comfy_api.py is located
        self.module_dir = Path(__file__).resolve().parent
        # Directory where /images and /workflows are located
        self.base_dir = Path(base_dir).resolve() if base_dir else self.module_dir

        self.workflows_dir = self.base_dir / "workflows"
        self.images_dir = self.base_dir / "images"

        self.workflow = None
        self.api_url = api_url
        self.pos_node_id = pos_node_id
        self.neg_node_id = neg_node_id
        self.resolution_id = resolution_id
        self.seed_node_id = seed_node_id

        # Resolve workflow path
        if workflow_path:
            wf = Path(workflow_path).expanduser()
            if not wf.is_absolute():
                wf = self.workflows_dir / workflow_path
            self.workflow_path = wf
        else:
            self.workflow_path = None
        self.load_workflow()

    def load_workflow(self):
        """
        Load the workflow JSON file and store it in the workflow attribute.
        
        Raises:
            Exception: If the workflow file cannot be loaded or parsed
        """
        try:
            with open(f'{self.workflow_path}', 'r') as file:
                workflow=json.load(file)

            self.workflow=workflow
        
        except Exception as e:
            print(f"Error loading workflow file: {e}")

    def queue_prompt(self, workflow):
        """
        Submit a workflow prompt to the ComfyUI API queue.
        
        Args:
            workflow (dict): The workflow configuration with prompts inserted
            
        Returns:
            dict: Response containing prompt_id if successful, None otherwise
        """
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
        """
        Download and save the generated image from the API response.
        
        Args:
            response (dict): The API response containing image information
            prompt_id (str): The prompt ID for this generation request
            
        Returns:
            str: Path to the saved image file if successful, None otherwise
        """

        for node_id, node_output in response.items():
            if "images" in node_output:
                for img in node_output["images"]:
                    filename = img["filename"]
                    subfolder = img["subfolder"]

                    try:
                        image_resp = requests.get(f"{self.api_url}/view?filename={filename}&subfolder={subfolder}&type=output", timeout=5)
                        new_filename = find_new_file_name(str(self.images_dir / filename))

                        with open(f"{new_filename}", "wb") as f:
                            f.write(image_resp.content)
                        print(f"Saved {new_filename}")
                        return new_filename
                    except Exception as e:
                        print(f"Failed to fetch image: {e}")
        return None

    def poll_for_result(self, prompt_id, timeout=20, interval=0.5):
        """
        Poll the API until the image generation is complete.
        
        Args:
            prompt_id (str): The prompt ID to check for completion
            timeout (int, optional): Maximum time to wait in seconds. Defaults to 20.
            interval (float, optional): Time between polling requests. Defaults to 0.5.
            
        Returns:
            dict: The outputs section of the completed prompt
            
        Raises:
            TimeoutError: If the prompt is not ready within the timeout period
        """
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

    def get_image(self, pos_prompt="Portrait of Super Mario and Doom Slayer", neg_prompt="", width=1024, height=1024, seed = randint(1,99999999)):
        """
        Generate an image using the provided prompts.
        
        This is the main method that orchestrates the entire image generation process:
        inserts prompts into workflow, queues the request, polls for completion,
        and fetches the resulting image.
        
        Args:
            pos_prompt (str): Positive prompt describing what to generate
            neg_prompt (str): Negative prompt describing what to avoid
            
        Returns:
            str: Path to the generated image file if successful, None otherwise
        """

        print(f"Received generation call: width: {width}, height: {height}, seed: {seed}")
        if not self.workflow:
            self.load_workflow()

        workflow = copy.deepcopy(self.workflow)

        # Insert positive and negative prompts into the loaded workflow
        workflow[f"{self.pos_node_id}"]["inputs"]["text"] = pos_prompt
        workflow[f"{self.neg_node_id}"]["inputs"]["text"] = neg_prompt
        workflow[f"{self.resolution_id}"]["inputs"]["width"] = str(width)
        workflow[f"{self.resolution_id}"]["inputs"]["height"] = str(height)
        workflow[f"{self.seed_node_id}"]["inputs"]["noise_seed"] = str(seed)

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


'''
def main():
    """Test function demonstrating basic usage of the Comfy class."""
    comfy = Comfy("workflows/sdxlturbo_example.json","http://127.0.0.1:8188",6,7,13)
    
    comfy.get_image("ultrarealistic, best quality photo of a woman with brown hair, indoor setting, natural lighting", "lowres, disfigured, error, mistake, missing limbs, low quality")

if __name__ == "__main__":
    main()
'''
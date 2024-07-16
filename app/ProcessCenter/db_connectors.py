import uuid
import rapidjson as json
import aiofiles
import os
from pathlib import Path


class MockdbConnector:
    
    def __init__(self, folder_path):
        self.folder_path =  folder_path
        
    def build_fodlers(self, connection_data, pipe_type, is_raw=False):
        pipe_id = connection_data.get(pipe_type, connection_data.get("id_api"))
        folder_type = pipe_type.split("_")[1]
        exchange = connection_data.get("exchange")
        folder_type_2 = "raw" if not is_raw else "processed"
        
        folder_path = Path("/".join([self.folder_path, folder_type_2, folder_type, exchange]))
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
        relative_file_path = "/".join([self.folder_path, folder_type_2, folder_type, exchange, pipe_id]) + ".json"
        return pipe_id, relative_file_path

    async def save(self, market_state, logger, pipe_type, data, connection_data, on_message:callable,):
        """  pipe_type : id_ws, id_api, id_api_2 """

        pipe_id = connection_data.get("id_api") if "id_api" in connection_data else connection_data.get("id_ws")

        try:

            data = json.loads(data)
            pipe_id, relative_file_path = self.build_fodlers(connection_data, pipe_type, False)

            # try:
            #     data = await on_message(data=data, market_state=market_state, connection_data=connection_data)
            #     pipe_id, relative_file_path = self.build_fodlers(connection_data, pipe_type, True)
            # except Exception as e:
            #     data = json.loads(data)
            #     pipe_id, relative_file_path = self.build_fodlers(connection_data, pipe_type, False)
            
            data["_doc"] = str(uuid.uuid4())
            
            if not os.path.exists(relative_file_path):
                async with aiofiles.open(relative_file_path, mode='w') as f:
                    content = [data]
                    await f.seek(0)
                    await f.truncate()
                    await f.write(json.dumps(content, indent=2))
            else:
                async with aiofiles.open(relative_file_path, mode='r+') as f:
                    try:
                        content = await f.read()
                        content = json.loads(content)
                    except json.JSONDecodeError as e:
                        print(f"JSONDecodeError reading file: {e}")
                        content = []

                    content.insert(0, data)
                    await f.seek(0)
                    await f.truncate()
                    await f.write(json.dumps(content, indent=2))
                    
        except FileNotFoundError as e:
            print(data)
            logger.error(f"FileNotFoundError of {pipe_id}: {e}")
        except PermissionError as e:
            print(data)
            logger.error(f"PermissionError of {pipe_id}: {e}")
        except IOError as e:
            print(data)
            logger.error(f"IOError handling file operations of {pipe_id}: {e}")
        except Exception as e:
            print(data)
            logger.error(f"Unexpected error handling file operations of {pipe_id}: {e}")
            


# Api Utils

Provides a common starting framework for all MTC backend APIs

# Installation

This module can be installed using pip as follows:

```
pip install git+ssh://git@gitlab.ethz.ch/mtc/libraries/api-utils.git
```

The same can also be achieved by adding the following block to your `requirements.txt` file:

```
# MTC API Utils package

git+ssh://git@gitlab.ethz.ch/mtc/libraries/api-utils.git
```

In order to import the `api-utils` library in a `Dockerfile`, add the relevant deployment SSH keys to your image beforehand.

# Earlier versions

The main branch generally contains the latest version of the `api-utils` library. If your API relies on an older version, you can access it by adding a branch
name or tag to the url as follows:

```
git+ssh://git@gitlab.ethz.ch/mtc/libraries/api-utils.git@v1
```

where `v1` is the branch/tag that should be used.

# Api-Utils Use Cases

The api-utils package provides several classes and functions that are helpful when setting up basic fastAPI servers for mtc projects. The following components
are available:

### api.py: BaseApi

BaseApi extends FastAPI with some common functionality used in the mtc api context. Call the constructor as follows to create a new BaseApi:

```python
app = BaseApi(is_ready=is_ready_function)
```

where is_ready is a function informing the Api whether the service, including the underlying models, is ready to receive requests.

BaseApi provides the following GET endpoints to check on the status of any service:

#### /

The home endpoint which merely displays a welcome message which can be configured using the BaseApi constructor

#### /liveness

The liveness endpoint is used in order to assert that the service is available and running. It returns a 200 OK status as well as a standardized message which
can be used to verify the service has been started correctly.

#### /readiness

The readiness endpoint calls the is_ready function passed to the BaseApi constructor in order to check if the service is ready to receive requests. This route
is called internally as well as by other services that rely on our api.

Additional endpoints can be added to the base api just like they would for any other fastApi app, e.g.:

```python
@api.get("/api/inference")
def inference_method():
    """ Endpoint implementation """
```

### api_client.py: ApiClient

The ApiClient is used by other python applications that call our api. These applications are usually either integration tests for the api or another api that
relies on the results of our api.

It provides the following methods to call the standard endpoints made available by the BaseApi class:

#### ApiClient.get_liveness

Calls the /liveness endpoint on the base_url of the client

#### ApiClient.get_readiness

Calls the /readiness endpoint on the base_url of the client

#### ApiClient.wait_for_service_readiness

Calls the /readiness endpoint on the base_url of the client repeatedly until it returns a 200 OK status. A timeout for this waiting loop can be set using the
parameter `timeout`.

### Implement your ApiClient

In order to extend the ApiClient for your API, simply extend the ApiClient class and add methods for your own endpoints. E.g:

```python
class ModelClient(ApiClient):

    @staticmethod
    def post_inference(body: ApiType) -> Tuple[requests.Response, ApiType]:
        response = requests.post(url=f"{self.BACKEND_URL}{test_inference_route}", json=body)

        response.raise_for_status()

        result = ApiType.from_dict(response.json())
        return response, result
```

### ApiType

TODO: Add documentation for `ApiType` based Pydantic models, inheritance, generic models, etc.

### Licence

Copyright 2022 ETH Zurich, Media Technology Center

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


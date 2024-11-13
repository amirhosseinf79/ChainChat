from locust import HttpUser, task

class LoadTestUser(HttpUser):
    headers = {
        "Authorization": "Bearer 82eaa1b5e50bd8ecf6f14d1fd892506df7c5bb61",
        "Content-Type": "application/json",
        # Add any other headers you need
    }

    @task
    def index(self):
        self.client.get("/", headers=self.headers)

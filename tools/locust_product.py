from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    wait_time = between(0.1, 2.5)

    @task
    def view_product(self):
        self.client.get("/api/products/")

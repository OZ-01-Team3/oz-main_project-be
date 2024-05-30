from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(0.1, 2.5)  # type: ignore

    @task
    def view_product(self) -> None:
        self.client.get("/api/products/")

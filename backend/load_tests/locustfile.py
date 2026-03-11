from locust import HttpUser, between, task


class OceanariumUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_health(self):
        self.client.get("/health")

    @task(5)
    def get_schedules(self):
        self.client.get("/schedules")

    @task(4)
    def get_guides(self):
        self.client.get("/guides")

    @task(4)
    def get_tours(self):
        self.client.get("/tours")

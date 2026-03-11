import sys

from locust import HttpUser, between, events, task

FAIL_RATIO_THRESHOLD = 0.01
AVG_RESPONSE_TIME_THRESHOLD = 500


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


@events.quitting.add_listener
def check_thresholds(environment, **_kwargs):
    stats = environment.stats.total
    if stats.num_requests == 0:
        return

    fail_ratio = stats.num_failures / stats.num_requests
    if fail_ratio > FAIL_RATIO_THRESHOLD:
        print(f"FAIL: fail ratio {fail_ratio:.2%} exceeds {FAIL_RATIO_THRESHOLD:.0%}")
        environment.process_exit_code = 1

    if stats.avg_response_time > AVG_RESPONSE_TIME_THRESHOLD:
        print(
            f"FAIL: avg response time {stats.avg_response_time:.0f}ms "
            f"exceeds {AVG_RESPONSE_TIME_THRESHOLD}ms"
        )
        environment.process_exit_code = 1

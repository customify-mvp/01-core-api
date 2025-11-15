"""Minimal Celery worker for debugging."""

from celery import Celery

# Minimal config
app = Celery(
    'test',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)


@app.task(name='test_task')
def test_task(x, y):
    """Simple test task."""
    print(f"🧪 Test task: {x} + {y} = {x+y}")
    return x + y


if __name__ == '__main__':
    # Test directly
    result = test_task.delay(2, 3)
    print(f"Task sent: {result.id}")
    print(f"Result: {result.get(timeout=10)}")
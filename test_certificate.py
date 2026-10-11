
from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home_endpoint_removed():
    response = client.get("/")
    assert response.status_code == 404


def test_bulk_certificate_generation():
    response = client.post(
        "/certificates/bulk",
        json={
            "recipients": [
                {
                    "name": "Test User",
                    "email": "test@example.com",
                    "course": "Python",
                }
            ]
        },
    )

    assert response.status_code == 200
    result = response.json()

    assert result["status"] == "completed"
    assert result["total_recipients"] == 1
    assert result["completed"] == 1

    certificate_id = result["generated_certificates"][0]["certificate_id"]

    download_response = client.get(
        f"/certificates/download/{certificate_id}"
    )
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"

    verify_response = client.get(f"/verify/{certificate_id}")
    assert verify_response.status_code == 200
    assert verify_response.json()["valid"] is True

    job_id = result["job_id"]
    zip_response = client.get(
        f"/certificates/bulk-download/{job_id}"
    )
    assert zip_response.status_code == 200
    assert zip_response.headers["content-type"] == "application/zip"


def test_invalid_bulk_request():
    response = client.post(
        "/certificates/bulk",
        json={"recipients": []},
    )
    assert response.status_code == 422


def test_job_not_found():
    response = client.get("/jobs/999999")
    assert response.status_code == 404


def test_invalid_certificate_id():
    response = client.get("/certificates/download/INVALID")
    assert response.status_code == 400


def test_individual_certificate_failure(monkeypatch):
    from app import main

    original_generate = main.generate_certificate

    def generate_with_one_failure(name, course, certificate_id):
        if name == "Fail User":
            raise RuntimeError("Simulated certificate generation failure")
        return original_generate(name, course, certificate_id)

    monkeypatch.setattr(
        main, "generate_certificate", generate_with_one_failure
    )

    response = client.post(
        "/certificates/bulk",
        json={
            "recipients": [
                {
                    "name": "Success User",
                    "email": "success@example.com",
                    "course": "Python",
                },
                {
                    "name": "Fail User",
                    "email": "fail@example.com",
                    "course": "Python",
                },
                {
                    "name": "Another Success",
                    "email": "another@example.com",
                    "course": "Networking",
                },
            ]
        },
    )

    assert response.status_code == 200
    result = response.json()

    assert result["completed"] == 2
    assert result["status"] == "partially_completed"
    assert len(result["generated_certificates"]) == 2
    assert len(result["failed_certificates"]) == 1


def test_job_creation_and_progress():
    response = client.post(
        "/certificates/bulk",
        json={
            "recipients": [
                {
                    "name": "Progress Test User",
                    "email": "progress@example.com",
                    "course": "Python",
                }
            ]
        },
    )

    assert response.status_code == 200
    result = response.json()
    job_id = result["job_id"]

    assert result["total_recipients"] == 1
    assert result["completed"] == 1
    assert result["status"] == "completed"

    progress_response = client.get(f"/jobs/{job_id}")
    assert progress_response.status_code == 200

    progress = progress_response.json()
    assert progress["job_id"] == job_id
    assert progress["total"] == 1
    assert progress["completed"] == 1
    assert progress["status"] == "completed"

    list_response = client.get("/jobs")
    assert list_response.status_code == 200
    assert any(
        job["job_id"] == job_id
        for job in list_response.json()
    )

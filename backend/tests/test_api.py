import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from fastapi.testclient import TestClient

from app.main import app


def test_complete_api_workflow():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "healthy", "ai_required": False}
        assert health.headers["x-content-type-options"] == "nosniff"
        assert health.headers["x-frame-options"] == "DENY"
        assert health.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"

        leads = client.get("/api/leads?sort=score_desc").json()
        assert len(leads) == 12
        assert all(lead["source"] == "Synthetic demo" for lead in leads)
        assert [lead["score"] for lead in leads] == sorted(
            [lead["score"] for lead in leads], reverse=True
        )
        assert all(lead["score_breakdown"] for lead in leads)
        assert all(lead["acquisition_rationale"] for lead in leads)
        assert all(lead["outreach_angle"] for lead in leads)

        expected_complete = sum(
            sum(lead[field] not in (None, "") for field in (
                "domain", "industry", "location", "employee_count", "year_founded", "description"
            ))
            for lead in leads
        ) / (len(leads) * 6) * 100
        assert client.get("/api/metrics").json()["data_completeness"] == round(expected_complete, 1)

        high_priority = client.get("/api/leads?priority=high").json()
        assert high_priority
        assert all(lead["priority"] == "high" for lead in high_priority)
        texas = client.get("/api/leads?search=Texas").json()
        assert texas
        assert all("texas" in (lead["location"] or "").lower() for lead in texas)
        ascending = client.get("/api/leads?sort=score_asc").json()
        assert [lead["score"] for lead in ascending] == sorted(lead["score"] for lead in ascending)
        alphabetical = client.get("/api/leads?sort=company").json()
        assert [lead["company_name"] for lead in alphabetical] == sorted(
            lead["company_name"] for lead in alphabetical
        )
        assert client.get("/api/leads?status=not-a-status").status_code == 422
        assert client.get("/api/leads?priority=urgent").status_code == 422
        assert client.get("/api/leads-export.csv?status=not-a-status").status_code == 422

        lead_id = leads[0]["id"]
        detail = client.get(f"/api/leads/{lead_id}")
        assert detail.status_code == 200
        assert client.get("/api/leads/999999").status_code == 404

        shortlisted = client.patch(
            f"/api/leads/{lead_id}/status", json={"status": "shortlisted"}
        )
        assert shortlisted.status_code == 200
        assert shortlisted.json()["status"] == "shortlisted"
        assert client.patch(
            f"/api/leads/{lead_id}/status", json={"status": "invalid"}
        ).status_code == 422
        assert client.get("/api/metrics").json()["shortlisted"] == 1
        workflow_segment = client.get("/api/leads?status=shortlisted").json()
        assert len(workflow_segment) == 1
        assert workflow_segment[0]["id"] == lead_id

        thesis = client.get("/api/thesis").json()
        invalid_thesis = {key: value for key, value in thesis.items() if key not in {"id", "updated_at"}}
        invalid_thesis.update({"employee_min": 101, "employee_max": 10})
        assert client.put("/api/thesis", json=invalid_thesis).status_code == 422

        aging_lead = next(lead for lead in leads if lead["company_name"] == "Sunbelt Safety Compliance")
        score_before = aging_lead["score"]
        updated_thesis = {key: value for key, value in thesis.items() if key not in {"id", "updated_at"}}
        updated_thesis["minimum_years"] = thesis["minimum_years"] + 5
        response = client.put("/api/thesis", json=updated_thesis)
        assert response.status_code == 200
        assert response.json()["minimum_years"] == updated_thesis["minimum_years"]
        score_after = client.get(f"/api/leads/{aging_lead['id']}").json()["score"]
        assert score_after < score_before

        csv_body = (
            "company_name,domain,industry,location,employee_count,year_founded,owner_name,email,phone,description\n"
            "Acceptance Services,acceptance.example,HVAC,Texas,22,2001,Ada Owner,ada@acceptance.example,+1-555-555-0199,Recurring maintenance\n"
        )
        imported = client.post(
            "/api/leads/import",
            files={"file": ("leads.csv", csv_body, "text/csv")},
        )
        assert imported.status_code == 200
        assert imported.json()["imported"] == 1
        imported_lead = client.get("/api/leads?search=Acceptance%20Services").json()[0]
        assert imported_lead["source"] == "CSV import"
        duplicate = client.post(
            "/api/leads/import",
            files={"file": ("leads.csv", csv_body, "text/csv")},
        )
        assert duplicate.json()["duplicates_skipped"] == 1
        duplicate_name_location = csv_body.replace(
            "acceptance.example", "different-domain.example"
        )
        assert client.post(
            "/api/leads/import",
            files={"file": ("leads.csv", duplicate_name_location, "text/csv")},
        ).json()["duplicates_skipped"] == 1

        assert client.post(
            "/api/leads/import", files={"file": ("leads.txt", b"data", "text/plain")}
        ).status_code == 400
        assert client.post(
            "/api/leads/import", files={"file": ("leads.csv", b"industry\nHVAC", "text/csv")}
        ).status_code == 422
        invalid_row = client.post(
            "/api/leads/import",
            files={"file": ("leads.csv", b"company_name,industry\n,HVAC", "text/csv")},
        )
        assert invalid_row.json()["invalid_rows"] == 1
        assert invalid_row.json()["errors"]
        invalid_values = client.post(
            "/api/leads/import",
            files={"file": (
                "leads.csv",
                b"company_name,employee_count,year_founded,website\nBad Data,abc,2999,javascript:alert(1)",
                "text/csv",
            )},
        )
        assert invalid_values.json()["invalid_rows"] == 1
        assert "employee_count must be a whole number" in invalid_values.json()["errors"][0]
        assert "year_founded must be between" in invalid_values.json()["errors"][0]
        assert "website must be an absolute" in invalid_values.json()["errors"][0]
        assert client.post(
            "/api/leads/import",
            files={"file": ("leads.csv", b"company_name\n\xff", "text/csv")},
        ).status_code == 400
        assert client.post(
            "/api/leads/import",
            files={"file": ("leads.csv", b"company_name\n" + b"a" * 5_000_001, "text/csv")},
        ).status_code == 413

        exported = client.get("/api/leads-export.csv?status=shortlisted")
        assert exported.status_code == 200
        assert "text/csv" in exported.headers["content-type"]
        assert exported.content.startswith(b"\xef\xbb\xbf")
        assert "source" in exported.text.splitlines()[0]
        assert leads[0]["company_name"] in exported.text

        formula_csv = (
            "company_name,domain,industry,location,employee_count,year_founded\n"
            "=2+2,formula-safe.example,HVAC,Texas,20,2000\n"
        )
        formula_import = client.post(
            "/api/leads/import", files={"file": ("formula.csv", formula_csv, "text/csv")}
        )
        assert formula_import.json()["imported"] == 1
        formula_lead = client.get("/api/leads?search=%3D2%2B2").json()[0]
        client.patch(f"/api/leads/{formula_lead['id']}/status", json={"status": "shortlisted"})
        safe_export = client.get("/api/leads-export.csv?status=shortlisted")
        assert "'=2+2" in safe_export.text

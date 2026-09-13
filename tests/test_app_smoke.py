from streamlit.testing.v1 import AppTest
from pathlib import Path


def test_all_governance_views_render_without_exception():
    pages=["Executive Overview","AI Inventory","Register AI Use Case","Risk Classification","Risk Assessment","Control Requirements","Lifecycle & Approval","Monitoring","Bias & Fairness","Human Oversight","Findings & Exceptions","Regulatory Mapping","Swiss Banking Context","Audit Trail"]
    app=AppTest.from_file(Path(__file__).parents[1]/"app.py",default_timeout=10).run()
    for page in pages:
        app.sidebar.radio[0].set_value(page)
        app.run()
        assert not app.exception, f"{page}: {app.exception}"

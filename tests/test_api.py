"""
Tests for the Mergington High School API endpoints.
"""

import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_success(self, client, reset_activities):
        """Test that get_activities returns all activities."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that all activities are returned
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert len(data) == 9
    
    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_participants_list(self, client, reset_activities):
        """Test that participants list is correctly returned."""
        response = client.get("/activities")
        data = response.json()
        
        chess_participants = data["Chess Club"]["participants"]
        assert isinstance(chess_participants, list)
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants
        assert len(chess_participants) == 2


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity."""
        client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        assert "newstudent@mergington.edu" in participants
        assert len(participants) == 3
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity."""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities."""
        # Sign up for Chess Club
        response1 = client.post(
            "/activities/Chess%20Club/signup?email=student@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(
            "/activities/Programming%20Class/signup?email=student@mergington.edu"
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        data = response.json()
        
        assert "student@mergington.edu" in data["Chess Club"]["participants"]
        assert "student@mergington.edu" in data["Programming Class"]["participants"]


class TestUnregister:
    """Tests for the POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant."""
        client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        assert "michael@mergington.edu" not in participants
        assert len(participants) == 1
        assert "daniel@mergington.edu" in participants
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister for an activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent%20Club/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_participant_not_signed_up(self, client, reset_activities):
        """Test unregister for a student not signed up for the activity."""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can sign up again after unregistering."""
        # Unregister
        client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        
        # Sign up again
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        
        # Verify signup successful
        get_response = client.get("/activities")
        data = get_response.json()
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestRootRedirect:
    """Tests for the root endpoint."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static HTML."""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegration:
    """Integration tests for multiple operations."""

    def test_signup_and_unregister_flow(self, client, reset_activities):
        """Test a complete signup and unregister flow."""
        email = "integration_test@mergington.edu"
        activity = "Basketball%20Team"
        
        # Get initial state
        initial = client.get("/activities").json()
        initial_count = len(initial["Basketball Team"]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        after_signup = client.get("/activities").json()
        assert len(after_signup["Basketball Team"]["participants"]) == initial_count + 1
        assert email in after_signup["Basketball Team"]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        after_unregister = client.get("/activities").json()
        assert len(after_unregister["Basketball Team"]["participants"]) == initial_count
        assert email not in after_unregister["Basketball Team"]["participants"]
    
    def test_availability_tracking(self, client, reset_activities):
        """Test that availability is correctly tracked."""
        activity_name = "Chess%20Club"
        
        # Get initial availability
        response = client.get("/activities")
        data = response.json()
        initial_participants = len(data["Chess Club"]["participants"])
        max_participants = data["Chess Club"]["max_participants"]
        
        assert initial_participants == 2
        assert max_participants == 12
        
        # Sign up new participant
        client.post(
            f"/activities/{activity_name}/signup?email=test@mergington.edu"
        )
        
        # Check updated availability
        response = client.get("/activities")
        data = response.json()
        updated_participants = len(data["Chess Club"]["participants"])
        
        assert updated_participants == initial_participants + 1

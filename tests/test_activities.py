"""Tests for FastAPI activity endpoints."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_success(self, client):
        """Test successfully retrieving all activities."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Verify activity structure
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_includes_participants(self, client):
        """Test that activities include participant information."""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client):
        """Test successfully signing up a new participant."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "anna@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "anna@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity."""
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "anna@mergington.edu"}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        assert "anna@mergington.edu" in chess_club["participants"]

    def test_signup_duplicate_participant_error(self, client):
        """Test that signing up the same person twice returns an error."""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "anna@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "anna@mergington.edu"}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_error(self, client):
        """Test that signing up for a non-existent activity returns 404."""
        response = client.post(
            "/activities/Fake Club/signup",
            params={"email": "anna@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_with_existing_participant(self, client):
        """Test that existing participants cannot sign up again."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()


class TestRemoveFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_delete_participant_success(self, client):
        """Test successfully removing a participant from an activity."""
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Removed" in data["message"]

    def test_delete_removes_participant(self, client):
        """Test that delete actually removes the participant from the activity."""
        client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" not in chess_club["participants"]

    def test_delete_nonexistent_activity_error(self, client):
        """Test that deleting from a non-existent activity returns 404."""
        response = client.delete(
            "/activities/Fake Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_delete_not_signed_up_error(self, client):
        """Test that deleting a participant not signed up returns 400."""
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "notasignedupuser@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()

    def test_delete_already_deleted_error(self, client):
        """Test that deleting the same participant twice returns an error."""
        # First delete
        response1 = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Second delete with same email
        response2 = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "not signed up" in data["detail"].lower()


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_signup_then_delete(self, client):
        """Test signing up then removing a participant."""
        # Sign up
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "anna@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Verify signup
        response_check = client.get("/activities")
        data_check = response_check.json()
        assert "anna@mergington.edu" in data_check["Chess Club"]["participants"]
        
        # Delete
        response2 = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "anna@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify deletion
        response_final = client.get("/activities")
        data_final = response_final.json()
        assert "anna@mergington.edu" not in data_final["Chess Club"]["participants"]

    def test_multiple_participants_signup(self, client):
        """Test multiple different participants can sign up."""
        emails = ["anna@mergington.edu", "bob@mergington.edu", "carol@mergington.edu"]
        
        for email in emails:
            response = client.post(
                "/activities/Chess Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        for email in emails:
            assert email in participants

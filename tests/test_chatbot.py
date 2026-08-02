"""Chatbot: sin API key de Groq usa el respaldo basado en reglas."""


def test_chat_empty_messages_returns_greeting(client):
    resp = client.post("/api/v1/chatbot/chat", json={"messages": [], "language": "es"})
    assert resp.status_code == 200
    assert "VineGuard AI" in resp.json()["response"]


def test_chat_greeting_es(client):
    resp = client.post("/api/v1/chatbot/chat", json={
        "messages": [{"role": "user", "content": "hola, ¿cómo estás?"}],
        "language": "es",
    })
    assert resp.status_code == 200
    assert "Hola" in resp.json()["response"]


def test_chat_diagnosis_question_es(client):
    resp = client.post("/api/v1/chatbot/chat", json={
        "messages": [{"role": "user", "content": "¿cómo puedo diagnosticar una hoja?"}],
        "language": "es",
    })
    assert resp.status_code == 200
    assert "Nuevo Diagnóstico" in resp.json()["response"]


def test_chat_english(client):
    resp = client.post("/api/v1/chatbot/chat", json={
        "messages": [{"role": "user", "content": "hello"}],
        "language": "en",
    })
    assert resp.status_code == 200
    assert resp.json()["response"]


def test_chat_portuguese(client):
    resp = client.post("/api/v1/chatbot/chat", json={
        "messages": [{"role": "user", "content": "olá"}],
        "language": "pt",
    })
    assert resp.status_code == 200
    assert resp.json()["response"]


def test_chat_invalid_language_falls_back_to_es(client):
    resp = client.post("/api/v1/chatbot/chat", json={
        "messages": [{"role": "user", "content": "hola"}],
        "language": "xx",
    })
    assert resp.status_code == 200
    assert "Hola" in resp.json()["response"]


def test_chat_multi_turn(client):
    resp = client.post("/api/v1/chatbot/chat", json={
        "messages": [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?"},
            {"role": "user", "content": "¿qué enfermedades detectas?"},
        ],
        "language": "es",
    })
    assert resp.status_code == 200
    assert "Black Rot" in resp.json()["response"]


def test_chat_uses_groq_when_available(client, monkeypatch):
    async def fake_groq(messages, language):
        return "Respuesta generada por el LLM de Groq"

    import backend.api.chatbot as chatbot_mod
    monkeypatch.setattr(chatbot_mod, "_call_groq", fake_groq)
    resp = client.post("/api/v1/chatbot/chat", json={
        "messages": [{"role": "user", "content": "hola"}],
        "language": "es",
    })
    assert resp.status_code == 200
    assert resp.json()["response"] == "Respuesta generada por el LLM de Groq"


def test_chat_falls_back_when_groq_fails(client, monkeypatch):
    async def fake_groq(messages, language):
        return None

    import backend.api.chatbot as chatbot_mod
    monkeypatch.setattr(chatbot_mod, "_call_groq", fake_groq)
    resp = client.post("/api/v1/chatbot/chat", json={
        "messages": [{"role": "user", "content": "hola"}],
        "language": "es",
    })
    assert resp.status_code == 200
    assert "Hola" in resp.json()["response"]

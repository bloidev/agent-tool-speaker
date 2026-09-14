# agent-tool-speaker

Proyecto para que luego de un mensaje enviado a claude, este lo lea usando la configuración del proyecto, normalmente creamos Claude.md y settings.local.json y se configuran dentro de tu carpeta para que realice esta acción, así como funciona esto tambien lo puedes adaptar para ejecutar el sonido de una notificación y funciones propias que iremos agregando con el tiempo.

1. crea tu Ambiente para tu proyecto con.

```sh
    python -m venv venv
```

2.  activalo con

```sh
venv\Scripts\Activate.ps1
```

3.  ejecutalo, levantara el servicio en puerto 8000

```sh
    py .\main.py
```

4.  prueba que funcione con curl

```sh
    curl -X POST http://127.0.0.1:8000/speak -H "Content-Type: application/json" -d "{`"text`": `"¡Hola! ¿Cómo estás?`"}"
```

5. agrega el control de hooks en tu agente claude por ejemplo con

settings.local.json

```json
{
  "permissions": {
    "allow": [
      "Bash(git rm *)",
      "Bash(git commit -m 'cleanup: remove documentation files \\(move to Obsidian\\) *)",
      "Bash(curl http://127.0.0.1:8000/speak *)"
    ]
  },
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python -c \"import sys, json, requests, io; sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8'); data=json.load(sys.stdin); text=data.get('last_assistant_message', 'Respuesta enviada'); requests.post('http://127.0.0.1:8000/speak', json={'text': text}, headers={'Content-Type': 'application/json; charset=utf-8'})\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash|Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r 'if .tool_response then \"Operación completada.\" else \"Procesando...\" end' 2>/dev/null || echo \"Listo.\"",
            "statusMessage": "Resumiendo respuesta"
          }
        ]
      }
    ]
  }
}
```

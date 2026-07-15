from google import genai

client = genai.Client(
    api_key=""
)

print("Listing Models:")
for m in client.models.list():
    if "embed" in m.name or "flash" in m.name or "pro" in m.name:
        print(f"{m.name} - {m.display_name}")

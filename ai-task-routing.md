# Gullicksen & Co. — AI Task Routing

## Task Force Ripper (Free/Cheap)
**Model:** Llama 3.1 70B (free via OpenRouter)
**Use for:**
- Listing descriptions
- Email drafts
- Social media posts
- Lead responses
- Contact cleanup
- Quick calculations
- Template-based work

## Task Force Papa Bear (Complex)
**Model:** Claude 3.5 Sonnet (via OpenRouter)
**Use for:**
- Strategy & branding
- Market analysis
- Document creation
- Complex reports
- Research & analysis

## Cost Comparison

| Task | Model | Cost |
|------|-------|------|
| Property descriptions | Llama 3.1 70B | Free |
| Email drafts | Llama 3.1 70B | Free |
| Social media posts | Llama 3.1 70B | Free |
| Contact cleanup | Llama 3.1 70B | Free |
| Lead responses | Llama 3.1 70B | Free |
| Market analysis | Claude 3.5 Sonnet | ~$0.15 |
| Strategy/branding | Claude 3.5 Sonnet | ~$0.15 |
| Complex documents | Claude 3.5 Sonnet | ~$0.15 |

## How It Works
- Simple tasks → Task Force Ripper (free)
- Complex tasks → Task Force Papa Bear (premium)
- Automatic routing based on task type
- One OpenRouter key, multiple models

## Configuration
Model aliases to add to config.yaml:
```yaml
aliases:
  task-force-ripper: "openrouter/meta-llama/llama-3.1-70b-instruct"
  task-force-papa-bear: "openrouter/anthropic/claude-3.5-sonnet"
```

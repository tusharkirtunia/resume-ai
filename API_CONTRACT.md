# Resume AI — API Contract (Frozen)

## Stability Guarantee
All endpoints listed below are considered stable.
Breaking changes require a major version bump.

---

## POST /api/variant/score
Input:
{
  "job": string
}

Output:
{
  "variant": string,
  "base_score": number,
  "variant_score": number,
  "improvement": number
}

---

## POST /api/variant/bullet-impact
Input:
{
  "job": string
}

Output:
{
  "variant": string,
  "impacts": [
    {
      "experience_index": number,
      "bullet_index": number,
      "bullet": string,
      "impact": number
    }
  ]
}

---

## POST /api/variant/bullet-decisions
Input:
{
  "job": string
}

Output:
{
  "variant": string,
  "decisions": [
    {
      "experience_index": number,
      "bullet_index": number,
      "bullet": string,
      "impact": number,
      "action": "KEEP" | "REWRITE" | "REMOVE"
    }
  ]
}
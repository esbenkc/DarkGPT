# Seemingly Human: Dark Patterns in ChatGPT

Our core question is:

> What are the risks for business models of large language model companies, such as OpenAI, to incentivize dark patterns and **reduce human autonomy**?
> and do these risks already show up in today's ChatGPT interactions?

## Experiments

We are interested in spotting where there are misalignments between what the user wants and what OpenAI's incentives are. In many cases, the user's objectives are subject to interference with corporate incentives. A few examples of _potential_ dark patterns include:

- **Data collection:** Injection of novelty and control of the conversation to get out-of-distribution data
- **Market expansion:** Conversation data collection to spot and extract negative
- **Regulatory compliance:** Hiding or controlling conversation to deny and hide privacy violations and establish rapport with the user
- **Data collection:** Bundling of privacy settings and unnecessary utility reduction ✅
- **User retention:** Making the chatbot become friendly with the human
- **Cost optimization:** Through technological dominance, OpenAI can reduce the performance of ChatGPT to make it _as attractive as needed_ instead of as good as it can be, so users don't use it more than they need - this reduces OpenAI's compute costs
- **Cost optimization:** Making the answers shorter than they need to be to reduce compute costs
- **Privacy Zuckering:** Encouraging users to share more personal information than they intend to through "helpful and honest" assistance (e.g. financial, medical, and legal)
- **Cost optimization:** Selling "latent advertisements" that emphasizes paying brands more than the functionally best brands ❌[^1]
- **Brand awareness:** Controlling the narrative around OpenAI as a company and ChatGPT as a service vs. other services
- **Innovation of service:** Pretend to create new model versions that are better even if they are not better but instead help the bottom line of OpenAI
- **User retention:** Echo chambers and filter bubbles to reinforce existing beliefs so the user is not offended and there are no risks for them to leave the service
- **Market expansion:** Reducing transparency and avoiding compliance with model sharing requests

[^1]: According to law, OpenAI would have to report this. E.g. UCPD in Europe requires that commercial intent be clearly recognizable in all advertising. Legally, you still might be able to do it by the statement "oh, we're just adjusting the weights" outside of retrieval-augmented ads.

### User objectives

The user's objectives are domain-based, such as:

| Domain                     | Objective                                                | Risks |
| -------------------------- | -------------------------------------------------------- | ----- |
| Learning                   | Factual, guided, and helpful information                 | 🟢    |
| Fact-Checking              | Concrete, retrieval-augmented, and truthful information  | 🟢    |
| Technical Support          | Clear, detailed, and problem-solving guidance            | 🟡    |
| Personal Assistant         | Efficient, task-oriented, and accurate assistance        | 🟡    |
| Therapeutic                | Empathetic, guiding, and harmless                        | 🟡    |
| Emotional Support          | Compassionate, understanding, and non-judgmental support | 🟡    |
| Health Advice              | Accurate, reliable, and safe guidance                    | 🟡    |
| Soliciting Criminal Advice | Assistive, proactive, and malicious                      | 🔴    |

### Company incentives

| Incentive             | Objective                                                   | Considerations                                                        | Priority |
| --------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------- | -------- |
| User Retention        | Maximize continuous engagement and subscription renewals    | Balancing engagement without fostering addictive behaviors            | ⬆        |
| Upselling Features    | Introduce premium features or tiers to increase revenue     | Ensuring core value remains accessible at lower tiers                 | ⬆⬆       |
| Data Collection       | Gather user data for improving services and personalization | Privacy concerns and securing user data against breaches              | ⬆⬆⬆      |
| User Satisfaction     | Deliver high-quality, reliable, and timely responses        | Aligning AI responses with user expectations and ethical guidelines   | ⬆        |
| Cost Optimization     | Efficiently manage operational costs to maximize profit     | Balancing cost-saving with maintaining service quality                | ⬆⬆       |
| Market Expansion      | Attract a diverse user base to expand market share          | Tailoring services to meet varied needs without diluting brand        | ⬆        |
| Innovation            | Continuously improve and innovate the AI model              | Investing in R&D while ensuring stability and reliability of service  | ⬆⬆⬆      |
| Community Building    | Foster a loyal user community around the service            | Engaging users in a manner that promotes positive interaction         | ⬆        |
| Brand Positioning     | Establish the service as a leader in AI chat solutions      | Differentiating the service through unique features or ethical stance | ⬆⬆       |
| Regulatory Compliance | Adhere to legal and ethical standards in AI deployment      | Navigating evolving regulations without stifling innovation           | ⬆⬆       |

/**
 * AIAnalyzer - Claude-powered intelligent vulnerability analysis
 * Performs deep analysis, pattern recognition, and generates recommendations
 */

const Anthropic = require('@anthropic-ai/sdk');
const fs = require('fs').promises;
const path = require('path');
const Logger = require('./Logger');

class AIAnalyzer {
    constructor(config = {}) {
        this.config = {
            model: config.model || 'claude-sonnet-4-5-20250929',
            maxTokens: config.maxTokens || 16000,
            temperature: config.temperature || 0,
            verbosity: config.verbosity || 'normal',
            ...config
        };

        this.logger = new Logger(this.config.verbosity);

        // Initialize Anthropic client
        this.anthropic = new Anthropic({
            apiKey: process.env.ANTHROPIC_API_KEY
        });

        // Load vulnerability knowledge base
        this.vulnerabilityKB = null;
    }

    /**
     * Main analysis method
     */
    async analyze({ findings, sourceFiles, chain, projectPath }) {
        try {
            this.logger.info('🧠 Performing AI-powered analysis...');

            // Load vulnerability knowledge base
            await this.loadVulnerabilityKB();

            // Group and correlate findings
            const groupedFindings = this.groupFindings(findings);

            // Analyze each group
            const analyses = [];
            for (const [category, categoryFindings] of Object.entries(groupedFindings)) {
                const analysis = await this.analyzeCategory({
                    category,
                    findings: categoryFindings,
                    sourceFiles,
                    chain
                });
                analyses.push(analysis);
            }

            // Cross-reference analysis
            const crossReference = await this.crossReferenceAnalysis(analyses, findings);

            // Risk assessment
            const riskAssessment = await this.assessOverallRisk(analyses, findings);

            // Generate recommendations
            const recommendations = await this.generateRecommendations(analyses, riskAssessment);

            return {
                summary: {
                    totalFindings: findings.length,
                    criticalIssues: findings.filter(f => f.severity === 'critical').length,
                    highIssues: findings.filter(f => f.severity === 'high').length,
                    overallRisk: riskAssessment.level,
                    confidence: riskAssessment.confidence
                },
                groupedFindings,
                analyses,
                crossReference,
                riskAssessment,
                recommendations,
                metadata: {
                    model: this.config.model,
                    analysisTime: new Date(),
                    chain
                }
            };

        } catch (error) {
            this.logger.error(`AI analysis failed: ${error.message}`);
            throw error;
        }
    }

    /**
     * Load vulnerability knowledge base
     */
    async loadVulnerabilityKB() {
        if (this.vulnerabilityKB) return;

        try {
            const kbPath = path.join(__dirname, '../../docs/VULNERABILITIES.md');
            this.vulnerabilityKB = await fs.readFile(kbPath, 'utf-8');
        } catch (error) {
            this.logger.warn('Could not load vulnerability knowledge base');
            this.vulnerabilityKB = '';
        }
    }

    /**
     * Group findings by category
     */
    groupFindings(findings) {
        const grouped = {};

        for (const finding of findings) {
            const category = finding.category || 'uncategorized';
            if (!grouped[category]) {
                grouped[category] = [];
            }
            grouped[category].push(finding);
        }

        return grouped;
    }

    /**
     * Analyze a category of findings using Claude
     */
    async analyzeCategory({ category, findings, sourceFiles, chain }) {
        this.logger.verbose(`Analyzing category: ${category}`);

        const prompt = this.buildCategoryAnalysisPrompt({
            category,
            findings,
            sourceFiles,
            chain
        });

        const response = await this.anthropic.messages.create({
            model: this.config.model,
            max_tokens: this.config.maxTokens,
            temperature: this.config.temperature,
            messages: [{
                role: 'user',
                content: prompt
            }]
        });

        const analysisText = response.content[0].text;

        return {
            category,
            findingsCount: findings.length,
            analysis: this.parseAnalysis(analysisText),
            rawAnalysis: analysisText
        };
    }

    /**
     * Build prompt for category analysis
     */
    buildCategoryAnalysisPrompt({ category, findings, sourceFiles, chain }) {
        const findingsContext = findings.map((f, i) => {
            return `
### Finding ${i + 1}
**Tool**: ${f.tool}
**Severity**: ${f.severity}
**Title**: ${f.title || f.description?.substring(0, 100)}
**Description**: ${f.description}
**Location**: ${f.file}:${f.line || 'unknown'}
**Code Snippet**:
\`\`\`
${f.codeSnippet || 'Not available'}
\`\`\`
`;
        }).join('\n---\n');

        return `You are a blockchain security expert analyzing smart contract vulnerabilities.

# Task
Analyze the following ${category} vulnerabilities found in a ${chain} smart contract project.

# Context
${this.getVulnerabilityContext(category)}

# Findings to Analyze
${findingsContext}

# Analysis Requirements
Please provide:

1. **Severity Assessment**: Are these findings accurately categorized? Should any be upgraded/downgraded?

2. **False Positive Analysis**: Which findings might be false positives and why?

3. **Exploitability**: For each real vulnerability, explain:
   - How it could be exploited
   - Prerequisites for exploitation
   - Potential impact

4. **Root Cause Analysis**: What coding patterns or design decisions led to these issues?

5. **Interconnections**: Do any findings relate to each other or compound the risk?

6. **Prioritization**: Which issues should be fixed first?

7. **Remediation**: Provide specific code fixes or mitigation strategies.

Format your response with clear sections and actionable recommendations.`;
    }

    /**
     * Get vulnerability context from knowledge base
     */
    getVulnerabilityContext(category) {
        if (!this.vulnerabilityKB) {
            return 'No additional context available.';
        }

        // Extract relevant section from knowledge base
        const categoryLower = category.toLowerCase();
        const lines = this.vulnerabilityKB.split('\n');
        let context = '';
        let inRelevantSection = false;
        let sectionDepth = 0;

        for (const line of lines) {
            const headerMatch = line.match(/^(#{1,6})\s+(.+)/);

            if (headerMatch) {
                const [, hashes, title] = headerMatch;
                const depth = hashes.length;

                if (title.toLowerCase().includes(categoryLower)) {
                    inRelevantSection = true;
                    sectionDepth = depth;
                    context += line + '\n';
                } else if (inRelevantSection && depth <= sectionDepth) {
                    break;
                }
            } else if (inRelevantSection) {
                context += line + '\n';
                if (context.length > 3000) break; // Limit context size
            }
        }

        return context || 'No specific context found for this category.';
    }

    /**
     * Parse AI analysis response
     */
    parseAnalysis(text) {
        const sections = {};
        let currentSection = 'general';
        let currentContent = '';

        const lines = text.split('\n');
        for (const line of lines) {
            const sectionMatch = line.match(/^#+\s*\*?\*?(.+?)\*?\*?:?\s*$/);

            if (sectionMatch) {
                if (currentContent.trim()) {
                    sections[currentSection] = currentContent.trim();
                }
                currentSection = sectionMatch[1].toLowerCase().replace(/\s+/g, '_');
                currentContent = '';
            } else {
                currentContent += line + '\n';
            }
        }

        if (currentContent.trim()) {
            sections[currentSection] = currentContent.trim();
        }

        return sections;
    }

    /**
     * Cross-reference analysis across categories
     */
    async crossReferenceAnalysis(analyses, allFindings) {
        const prompt = `You are analyzing the interconnections between different vulnerability categories found in a smart contract audit.

# Vulnerability Categories Analyzed
${analyses.map(a => `- ${a.category} (${a.findingsCount} findings)`).join('\n')}

# Task
Identify:
1. **Compounding Risks**: Which vulnerabilities could be combined for a more severe attack?
2. **Attack Chains**: What multi-step attack scenarios are possible?
3. **Common Root Causes**: Are there systemic issues causing multiple vulnerability types?
4. **Hidden Risks**: Are there potential issues not caught by the tools that could exist given these findings?

Provide a concise analysis focusing on the most critical interconnections.`;

        const response = await this.anthropic.messages.create({
            model: this.config.model,
            max_tokens: 4000,
            temperature: this.config.temperature,
            messages: [{ role: 'user', content: prompt }]
        });

        return {
            analysis: response.content[0].text,
            timestamp: new Date()
        };
    }

    /**
     * Assess overall risk level
     */
    async assessOverallRisk(analyses, findings) {
        const criticalCount = findings.filter(f => f.severity === 'critical').length;
        const highCount = findings.filter(f => f.severity === 'high').length;

        const prompt = `Assess the overall security risk of a smart contract with:
- ${criticalCount} critical vulnerabilities
- ${highCount} high severity vulnerabilities
- ${findings.length} total findings

Categories affected: ${analyses.map(a => a.category).join(', ')}

Provide:
1. Overall risk level (CRITICAL/HIGH/MEDIUM/LOW)
2. Confidence in this assessment (HIGH/MEDIUM/LOW)
3. Brief justification (2-3 sentences)
4. Deployment recommendation (DO NOT DEPLOY / FIX CRITICAL ISSUES FIRST / ACCEPTABLE WITH MITIGATIONS / READY)

Format as JSON:
{
  "level": "...",
  "confidence": "...",
  "justification": "...",
  "deploymentRecommendation": "..."
}`;

        const response = await this.anthropic.messages.create({
            model: this.config.model,
            max_tokens: 1000,
            temperature: 0,
            messages: [{ role: 'user', content: prompt }]
        });

        try {
            const jsonMatch = response.content[0].text.match(/\{[\s\S]+\}/);
            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            }
        } catch (error) {
            this.logger.warn('Could not parse risk assessment JSON');
        }

        return {
            level: criticalCount > 0 ? 'CRITICAL' : highCount > 0 ? 'HIGH' : 'MEDIUM',
            confidence: 'MEDIUM',
            justification: 'Automated assessment based on finding counts',
            deploymentRecommendation: criticalCount > 0 ? 'DO NOT DEPLOY' : 'FIX CRITICAL ISSUES FIRST'
        };
    }

    /**
     * Generate actionable recommendations
     */
    async generateRecommendations(analyses, riskAssessment) {
        const prompt = `Based on the security analysis, generate prioritized recommendations.

Overall Risk: ${riskAssessment.level}

# Analysis Summary
${analyses.map(a => `**${a.category}**: ${a.findingsCount} findings`).join('\n')}

Generate:
1. **Immediate Actions** (must fix before deployment)
2. **High Priority** (fix in next iteration)
3. **Medium Priority** (fix when possible)
4. **Best Practices** (long-term improvements)

For each recommendation, include:
- Specific action
- Why it matters
- Estimated effort (hours/days)

Keep recommendations actionable and specific.`;

        const response = await this.anthropic.messages.create({
            model: this.config.model,
            max_tokens: 4000,
            temperature: this.config.temperature,
            messages: [{ role: 'user', content: prompt }]
        });

        return {
            text: response.content[0].text,
            generated: new Date()
        };
    }
}

module.exports = AIAnalyzer;

from typing import Optional, List, Dict
from utils.anthropic_client import AnthropicClient
from models.paper import Paper, AgentConversation
from models.topic import Topic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import json


class AgentOrchestrator:
    """Multi-agent orchestrator for paper generation"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = AnthropicClient()
        self.agent_roles = [
            "research_director",
            "literature_researcher",
            "methodology_expert",
            "data_analyst",
            "paper_writer",
            "peer_reviewer",
        ]

    async def generate_paper(
        self,
        topic_id: int,
        paper_id: Optional[int] = None,
        progress_callback=None,
    ) -> Paper:
        """
        Orchestrate multi-agent paper generation workflow

        Args:
            topic_id: The research topic ID
            paper_id: Optional existing paper ID to use
            progress_callback: Optional callback for progress updates

        Returns:
            Generated Paper object
        """

        # Get topic
        topic = await self._get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")

        # Get or Create paper record
        if paper_id:
            result = await self.db.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                raise ValueError(f"Paper {paper_id} not found")
            paper.status = "processing"
        else:
            paper = Paper(
                topic_id=topic_id,
                title=f"Research on {topic.title}",
                status="processing",
            )
            self.db.add(paper)
        
        await self.db.commit()
        await self.db.refresh(paper)

        # Context accumulation
        context = {
            "topic": topic.to_dict(),
            "literature_review": "",
            "methodology": "",
            "data_analysis": "",
            "draft": "",
            "review": "",
        }

        try:
            # Step 1: Research Director Analysis
            await self._update_progress(progress_callback, "research_director", "working", 10)
            director_analysis = await self._run_agent(
                "research_director",
                f"分析以下研究选题，制定研究计划：\n\n"
                f"标题: {topic.title}\n"
                f"描述: {topic.description}\n"
                f"领域: {topic.field}\n"
                f"关键词: {', '.join(json.loads(topic.keywords) if topic.keywords else [])}",
                paper.id,
                step_name="Research Plan"
            )
            await self._update_progress(progress_callback, "research_director", "completed", 15)

            # Step 2: Literature Research
            await self._update_progress(progress_callback, "literature_researcher", "working", 20)
            literature_review = await self._run_agent(
                "literature_researcher",
                f"基于以下研究计划，进行文献调研：\n\n{director_analysis}\n\n"
                f"请搜索相关文献，总结研究现状、关键发现和研究空白。",
                paper.id,
                step_name="Literature Review"
            )
            context["literature_review"] = literature_review
            await self._update_progress(progress_callback, "literature_researcher", "completed", 35)

            # Step 3: Methodology Design
            await self._update_progress(progress_callback, "methodology_expert", "working", 40)
            methodology = await self._run_agent(
                "methodology_expert",
                f"基于文献调研结果，设计研究方法：\n\n{literature_review}\n\n"
                f"请提供详细的研究方法、实验设计和数据采集方案。",
                paper.id,
                step_name="Methodology Design"
            )
            context["methodology"] = methodology
            await self._update_progress(progress_callback, "methodology_expert", "completed", 50)

            # Step 4: Data Analysis Plan
            await self._update_progress(progress_callback, "data_analyst", "working", 55)
            data_analysis = await self._run_agent(
                "data_analyst",
                f"基于研究方法，提供数据分析方案：\n\n{methodology}\n\n"
                f"请建议统计方法、数据可视化方案和结果验证方法。",
                paper.id,
                step_name="Data Analysis Plan"
            )
            context["data_analysis"] = data_analysis
            await self._update_progress(progress_callback, "data_analyst", "completed", 65)

            # Step 5: Paper Writing
            await self._update_progress(progress_callback, "paper_writer", "working", 70)
            draft_content = await self._run_agent(
                "paper_writer",
                f"基于以上所有信息，撰写完整的学术论文：\n\n"
                f"## 研究计划\n{director_analysis}\n\n"
                f"## 文献综述\n{literature_review}\n\n"
                f"## 研究方法\n{methodology}\n\n"
                f"## 数据分析\n{data_analysis}\n\n"
                f"请撰写包含标题、摘要、引言、方法、结果、讨论、结论和参考文献的完整论文。使用Markdown格式。",
                paper.id,
                step_name="First Draft"
            )
            context["draft"] = draft_content
            await self._update_progress(progress_callback, "paper_writer", "completed", 85)

            # Step 6: Peer Review & Revision Loop
            max_iterations = 5  # 最大修改轮数
            current_iteration = 0
            quality_score = 0.0

            # 初始评审
            await self._update_progress(progress_callback, "peer_reviewer", "working", 90)
            review_result = await self._run_agent(
                "peer_reviewer",
                f"请严格评审以下论文：\n\n{draft_content}\n\n"
                f"请按照国际顶级期刊标准评审，提供评分和改进建议。",
                paper.id,
                iteration=current_iteration + 1,
                step_name="Initial Peer Review"
            )
            context["review"] = review_result

            # Extract quality score from JSON or Fallback
            quality_score = self._extract_quality_score(review_result)

            # Revision Loop
            while quality_score < 90 and current_iteration < max_iterations:
                current_iteration += 1
                print(f"Quality score {quality_score} is below 90. Starting revision round {current_iteration}...")

                # Dynamic Progress Update
                progress_percent = 90 + (current_iteration / max_iterations) * 5
                await self._update_progress(
                    progress_callback,
                    "paper_revisor",
                    "working",
                    progress_percent,
                    message=f"Optimizing paper (Round {current_iteration}/5, Score: {quality_score})"
                )

                # 1. Revision Agent
                revision_task = (
                    f"这是当前的论文草稿：\n\n{draft_content}\n\n"
                    f"这是同行评审的意见（当前评分 {quality_score}）：\n\n{review_result}\n\n"
                    f"请根据以上意见，重新修改并完善整篇论文，目标是使评分达到 90 分以上。"
                )

                draft_content = await self._run_agent(
                    "paper_revisor",
                    revision_task,
                    paper.id,
                    iteration=current_iteration,
                    step_name=f"Revision Round {current_iteration}"
                )

                # 2. Re-Review
                await self._update_progress(
                    progress_callback,
                    "peer_reviewer",
                    "reviewing_revision",
                    progress_percent + 1,
                    message=f"Reviewing revision {current_iteration}..."
                )

                review_result = await self._run_agent(
                    "peer_reviewer",
                    f"这是根据您之前的意见修改后的论文版本：\n\n{draft_content}\n\n"
                    f"请重新进行严格评审和评分。之前的意见是：{review_result}",
                    paper.id,
                    iteration=current_iteration + 1,
                    step_name=f"Peer Review Round {current_iteration}"
                )

                # Update Score
                quality_score = self._extract_quality_score(review_result)
                context["review"] = review_result

            # Log final status
            if quality_score >= 90:
                print(f"Success! Reached target score: {quality_score}")
            else:
                print(f"Warning: Max iterations reached. Final score: {quality_score}")

            await self._update_progress(progress_callback, "peer_reviewer", "completed", 98)

            # Update paper with final content
            paper.content = draft_content
            paper.abstract = self._extract_abstract(draft_content)
            paper.quality_score = quality_score
            paper.status = "completed"

            await self.db.commit()
            await self.db.refresh(paper)

            # CRITICAL: Send progress update AFTER saving the paper content
            await self._update_progress(progress_callback, "completed", "completed", 100)

            return paper

        except Exception as e:
            print(f"Error in paper generation: {e}")
            paper.status = "error"
            await self.db.commit()
            raise

    async def _run_agent(
        self,
        role: str,
        task: str,
        paper_id: int,
        iteration: int = 1,
        step_name: str = None,
    ) -> str:
        """Run a single agent and save conversation"""

        response = await self.client.create_message(
            role=role,
            context="",
            task=task,
        )

        # Extract signature and clean content
        model_signature, cleaned_content = self._extract_signature_and_clean(response)

        # Save conversation with traceability info
        conversation = AgentConversation(
            paper_id=paper_id,
            agent_role=role,
            message=cleaned_content, # Save cleaned content
            iteration=iteration,
            step_name=step_name or role,
            input_context=task, # Save the input task as context
            model_signature=model_signature
        )
        self.db.add(conversation)
        await self.db.commit()

        return cleaned_content

    def _extract_signature_and_clean(self, content: str):
        """Extract model signature from the last line and return cleaned content"""
        lines = content.strip().split('\n')
        signature = None
        cleaned_content = content

        # Check last line for signature
        if lines:
            last_line = lines[-1].strip()
            if last_line.startswith("-- Generated by") and last_line.endswith("--"):
                signature = last_line
                # Remove the signature line
                cleaned_content = '\n'.join(lines[:-1]).strip()

        # Fallback if not found
        if not signature:
            # Use default model from client if available
            signature = f"-- Generated by {self.client.model} (Fallback) --"

        return signature, cleaned_content

    async def _get_topic(self, topic_id: int) -> Optional[Topic]:
        """Get topic by ID"""
        result = await self.db.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        return result.scalar_one_or_none()

    async def _update_progress(self, callback, agent: str, status: str, progress: int, message: str = None):
        """Update progress via callback"""
        if callback:
            msg = message if message else f"{agent} is {status}"
            await callback({
                "agent": agent,
                "status": status,
                "progress": progress,
                "message": msg,
            })

    def _extract_quality_score(self, review: str) -> float:
        """Extract quality score from review text (JSON priority)"""
        import re
        import json

        # 1. Try parsing JSON first (Most reliable)
        try:
            # Find JSON block using regex if mixed with text
            json_match = re.search(r'\{.*\}', review, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                if "scores" in data and "total" in data["scores"]:
                    return float(data["scores"]["total"])
                # Handle flat structure fallback
                if "total_score" in data:
                    return float(data["total_score"])
                if "score" in data:
                    return float(data["score"])
        except Exception as e:
            print(f"JSON parsing failed for score extraction: {e}")

        # 2. Fallback to Regex patterns
        try:
            # Look for various patterns like "总分: 85", "Score: 90/100", "[88]"
            patterns = [
                r'"total":\s*(\d+(?:\.\d+)?)',  # "total": 85
                r'总分[：:]\s*(\d+(?:\.\d+)?)',
                r'评分[：:]\s*(\d+(?:\.\d+)?)',
                r'Score[：:]\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*/\s*100',
                r'\[\s*(\d+(?:\.\d+)?)\s*\]'
            ]

            for pattern in patterns:
                match = re.search(pattern, review, re.IGNORECASE)
                if match:
                    val = float(match.group(1))
                    if 0 <= val <= 100:
                        return val

            # 3. Last resort: find any reasonable number between 70 and 100
            numbers = re.findall(r'(\d+(?:\.\d+)?)', review)
            for n in numbers:
                val = float(n)
                if 70 <= val <= 100:
                    return val

            return 80.0  # Default reasonable score
        except:
            return 80.0

    def _extract_abstract(self, content: str) -> str:
        """Extract abstract from paper content"""
        try:
            import re
            # Look for Abstract section
            match = re.search(r'#+\s*(?:Abstract|摘要)\s*\n+(.*?)(?=\n#+|\Z)', content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()[:500]

            # Fallback: return first paragraph
            paragraphs = content.split('\n\n')
            for p in paragraphs:
                if len(p.strip()) > 50:
                    return p.strip()[:500]

            return "No abstract available"
        except:
            return "No abstract available"

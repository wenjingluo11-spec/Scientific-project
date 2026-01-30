import asyncio
import sys
import os
import json

# Add current directory to sys.path
sys.path.append(os.getcwd())

from models.database import async_session_maker
from services.orchestrator import AgentOrchestrator
from models.paper import Paper
from models.topic import Topic
from sqlalchemy import select

async def debug_generation():
    paper_id = 21 # Simulate a new paper ID
    topic_ids = [14] # Use a known good topic ID (from paper 18)

    print(f"Starting debug generation for Paper ID {paper_id}...")

    async with async_session_maker() as db:
        # Create a dummy paper entry
        result = await db.execute(select(Paper).where(Paper.id == 18)) # Copy from existing
        existing_paper = result.scalar_one_or_none()
        if not existing_paper:
            print("Paper 18 not found to copy from.")
            return

        # Simulate creation
        # We won't actually create a DB entry to avoid messing up ID sequences too much, 
        # or we can just instantiate the orchestrator and call generate_paper.
        # But generate_paper queries the DB for the paper object.
        
        # Let's create a temporary paper in DB
        topics_json = json.dumps(topic_ids)
        new_paper = Paper(
            id=paper_id,
            topic_id=topic_ids[0],
            topic_ids=topics_json,
            title="Debug Paper Generation",
            status="processing"
        )
        # Check if exists first
        exists = await db.get(Paper, paper_id)
        if exists:
            await db.delete(exists)
            await db.commit()
            
        db.add(new_paper)
        await db.commit()

        orchestrator = AgentOrchestrator(db)
        
        async def mock_progress(data):
            print(f"PROGRESS: {data}")

        try:
            print("Calling orchestrator.generate_paper...")
            await orchestrator.generate_paper(
                topic_ids=topic_ids,
                paper_id=paper_id,
                progress_callback=mock_progress
            )
            print("Generation completed successfully!")
        except Exception as e:
            print(f"CAUGHT EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_generation())

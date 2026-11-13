# storyinventory requests
1. pipeline/story/story.json: add surface `label` (max_words 4, story false, where "stat, setting and menu labels"), and note in tools/story_critic_prompt.md S6 that a label names a thing, not an action. tools/build/story_inventory.py surface_of then returns `label` for non-action <=4-word text. Clears about 40 critic fails.
2. pipeline/story/story-bible.md (Story role): add Names/canon for GDD SH1.0 mechanics shown in controls and shop labels (Absorb, Dash, Hop, spells, Suction, Lives), or a decision row, so S8 stops failing them.
3. Credits: Names-table rows for the three real credit names.

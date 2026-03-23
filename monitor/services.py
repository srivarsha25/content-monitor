import json
import os
from django.utils.dateparse import parse_datetime
from .models import Keyword, ContentItem, Flag


def load_mock_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(base_dir, 'mock_data.json')
    with open(filepath, 'r') as f:
        return json.load(f)


def compute_score(keyword_name, title, body):
    keyword = keyword_name.lower().strip()
    title_lower = title.lower()
    body_lower = body.lower()

    # Exact full title match
    if keyword == title_lower.strip():
        return 100

    # All words of keyword appear in title (multi-word support)
    keyword_words = keyword.split()
    title_words = title_lower.split()
    body_words = body_lower.split()

    if all(word in title_words for word in keyword_words):
        return 90

    # Partial keyword match in title (substring)
    if keyword in title_lower:
        return 70

    # All words of keyword appear in body
    if all(word in body_words for word in keyword_words):
        return 50

    # Keyword appears in body as substring
    if keyword in body_lower:
        return 40

    return 0        # no match


def run_scan():
    items = load_mock_data()
    keywords = Keyword.objects.all()
    created_count = 0
    skipped_count = 0

    for item_data in items:
        last_updated = parse_datetime(item_data['last_updated'])

        content_item, _ = ContentItem.objects.update_or_create(
            title=item_data['title'],
            source=item_data['source'],
            defaults={
                'body': item_data['body'],
                'last_updated': last_updated,
            }
        )

        for keyword in keywords:
            score = compute_score(keyword.name, content_item.title, content_item.body)

            if score == 0:
                continue

            existing_flag = Flag.objects.filter(
                keyword=keyword,
                content_item=content_item
            ).first()

            # Suppression rule:
            # If flag exists and was marked irrelevant,
            # only resurface it if the content has changed since it was marked
            if existing_flag:
                if existing_flag.status == 'irrelevant':
                    content_changed = (
                        existing_flag.content_snapshot is None or
                        content_item.last_updated > existing_flag.content_snapshot
                    )
                    if not content_changed:
                        skipped_count += 1
                        continue
                    else:
                        # Content changed — reset the flag
                        existing_flag.status = 'pending'
                        existing_flag.score = score
                        existing_flag.content_snapshot = content_item.last_updated
                        existing_flag.save()
                        created_count += 1
                        continue
                else:
                    # Already flagged as pending or relevant — update score only
                    existing_flag.score = score
                    existing_flag.save()
                    continue

            # No existing flag — create a new one
            Flag.objects.create(
                keyword=keyword,
                content_item=content_item,
                score=score,
                status='pending',
                content_snapshot=content_item.last_updated
            )
            created_count += 1

    return {'created': created_count, 'skipped': skipped_count}
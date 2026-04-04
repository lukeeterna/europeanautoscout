#!/usr/bin/env python3
"""
ARGOS — Generatore Immagini Luca Ferretti v2
Basato su deep research s100_imagen_veo3_best_practices.md

Modello: Imagen 4 Ultra via Vertex AI ($0.06/img, coperto da $300 free credits)
Budget stimato: ~$4 per 15 foto finali (60 generazioni con 4 varianti ciascuna)

Usage:
    python3 tools/generate_luca_ferretti_images.py              # genera tutte
    python3 tools/generate_luca_ferretti_images.py --check      # solo verifica accesso API
    python3 tools/generate_luca_ferretti_images.py --fast        # usa Imagen 4 Fast (test, $0.02/img)
    python3 tools/generate_luca_ferretti_images.py --variants 1  # 1 variante (default: 4)
"""

import os
import sys
import time
import json
import base64
import subprocess
from pathlib import Path

# --- Config ---
PROJECT_ROOT = Path(__file__).parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "luca_ferretti"
SA_PATH = Path.home() / "Downloads" / "argos-gmail-491110-1590911e33f9.json"

PROJECT_ID = "argos-gmail-491110"
LOCATION = "us-central1"

# --- Descrizione facciale costante (applicata a OGNI prompt) ---
# Basata su best practice: stessa descrizione dettagliata in ogni prompt
# per massimizzare consistenza senza Subject Customization
FACE_DESC = (
    "an Italian man, 37 years old, short dark brown hair neatly styled and parted to the side, "
    "light stubble (2-3 day beard), warm brown eyes, olive Mediterranean complexion, "
    "medium-athletic build, natural slight asymmetry in features, "
    "visible pores and natural skin texture, subtle smile lines around eyes"
)

# --- Negative prompt (da research: evitare uncanny valley) ---
NEGATIVE_PROMPT = (
    "cartoon, anime, illustration, painting, drawing, sketch, 3d render, cgi, digital art, "
    "watermark, signature, logo, text overlay, "
    "plastic skin, waxy skin, poreless skin, airbrushed, oversmoothed, "
    "bad anatomy, deformed, extra limbs, asymmetrical face, "
    "yellow teeth, too many fingers, fused fingers, extra fingers, "
    "glassy eyes, dead eyes, soulless eyes, blurry, low quality, jpeg artifacts, "
    "perfect symmetrical features, mannequin, stock photo model"
)

# --- Le 15 foto (prompt ottimizzati secondo Google Prompt Guide) ---
# Formula: Subject + Action/Pose + Environment + Lighting + Camera/Style
PHOTO_SET = [
    # === RITRATTI (3) ===
    {
        "id": "P1",
        "filename": "luca_portrait_formal.jpg",
        "use": "LinkedIn profile, WA Business, Google Business, Trustpilot",
        "aspect_ratio": "1:1",
        "prompt": (
            f"Professional business headshot of {FACE_DESC}, "
            "wearing a well-fitted dark navy blazer over crisp white dress shirt, no tie, "
            "looking directly at camera with confident warm expression, "
            "neutral soft gray studio background with subtle gradient, "
            "shot on Canon EOS R5, 85mm f/1.4 portrait lens, shallow depth of field, "
            "professional studio three-point lighting with key light from left, "
            "photorealistic, natural skin texture with slight film grain, 4K detail"
        ),
    },
    {
        "id": "P2",
        "filename": "luca_portrait_desk.jpg",
        "use": "Landing hero, dossier PDF header, email signature",
        "aspect_ratio": "4:3",
        "prompt": (
            f"Professional business portrait of {FACE_DESC}, "
            "wearing charcoal gray suit with light blue open-collar shirt, "
            "seated at a modern wooden desk with laptop slightly visible, "
            "European city skyline through large floor-to-ceiling windows behind him, "
            "natural soft directional window light from the left, warm afternoon tones, "
            "shot on Canon EOS R5, 50mm f/2 standard lens, medium depth of field, "
            "photorealistic, professional photography, natural skin tones, slight warmth"
        ),
    },
    {
        "id": "P3",
        "filename": "luca_portrait_casual.jpg",
        "use": "Social media, alternative profile, WA status",
        "aspect_ratio": "1:1",
        "prompt": (
            f"Casual professional portrait of {FACE_DESC}, "
            "wearing dark navy polo shirt, relaxed confident posture, "
            "outdoor European urban setting with blurred modern architecture, "
            "golden hour natural light with warm tones, slight lens flare, "
            "shot on Sony A7R V, 35mm prime lens, wide aperture f/2.8, "
            "candid photography feel, not a studio shoot, "
            "photorealistic, natural noise, slight film grain, Kodak Portra 400 tones"
        ),
    },

    # === CONTESTI AUTO/SHOWROOM (4) ===
    {
        "id": "A1",
        "filename": "luca_showroom_bmw.jpg",
        "use": "Landing 'Chi Sono', WA Day 3 follow-up",
        "aspect_ratio": "16:9",
        "prompt": (
            f"Full body shot of {FACE_DESC}, "
            "wearing dark navy blazer over white shirt with dark chinos, "
            "standing confidently next to a white BMW X3 in a modern German car dealership showroom, "
            "clean glass and steel showroom interior, BMW logo signage subtly visible in background, "
            "bright even showroom lighting with reflections on polished floor, "
            "shot on Canon EOS R5, 35mm prime lens, f/4, full scene visible, "
            "professional automotive photography, photorealistic, natural skin texture"
        ),
    },
    {
        "id": "A2",
        "filename": "luca_inspecting_car.jpg",
        "use": "Dossier PDF interior, social post 'al lavoro'",
        "aspect_ratio": "4:3",
        "prompt": (
            f"Medium shot of {FACE_DESC}, "
            "wearing navy blazer, leaning slightly to inspect the interior dashboard of a silver Mercedes GLC, "
            "one hand on the open car door, focused concentrated professional expression, "
            "European outdoor car lot with other premium vehicles in background, overcast sky, "
            "shot on Canon EOS R5, 50mm f/2 lens, reportage photography style, "
            "photorealistic, documentary feel, natural overcast lighting, slight film grain"
        ),
    },
    {
        "id": "A3",
        "filename": "luca_piazzale_tedesco.jpg",
        "use": "LinkedIn cover photo (1584x396 crop), landing background",
        "aspect_ratio": "16:9",
        "prompt": (
            f"Wide shot of {FACE_DESC}, "
            "wearing navy blazer and dark jeans, walking through a large European outdoor car dealership, "
            "rows of premium vehicles visible (BMW, Audi, Mercedes), German commercial signage, "
            "overcast European weather, wet asphalt reflecting vehicles, "
            "shot on Canon EOS R5, 24mm wide angle lens, f/5.6, "
            "automotive industry reportage style, photorealistic, "
            "natural overcast soft lighting, slight desaturation"
        ),
    },
    {
        "id": "A4",
        "filename": "luca_audi_showroom.jpg",
        "use": "One-pager PDF, social media gallery",
        "aspect_ratio": "4:3",
        "prompt": (
            f"{FACE_DESC}, "
            "wearing navy blazer with white shirt, leaning casually against a black Audi Q5, "
            "one hand in trouser pocket, relaxed confident pose, looking at camera with slight smile, "
            "modern minimal German showroom interior, clean white walls, polished concrete floor, "
            "bright even artificial showroom lighting, "
            "shot on Sony A7R V, 85mm f/1.8, shallow depth of field, bokeh on car behind, "
            "photorealistic, professional, natural skin texture, candid professional moment"
        ),
    },

    # === CONTESTI BUSINESS/MEETING (4) ===
    {
        "id": "B1",
        "filename": "luca_handshake.jpg",
        "use": "Landing 'Chi Sono' trust signal, case study",
        "aspect_ratio": "4:3",
        "prompt": (
            f"Two businessmen in a modern glass-walled meeting room, the man on the left is {FACE_DESC} "
            "wearing navy blazer, shaking hands firmly with another European businessman in gray suit, "
            "both with genuine professional smiles, eye contact between them, "
            "clean modern office furniture, city view through windows, "
            "soft natural window light from the right, "
            "shot on Canon EOS R5, 50mm f/2.8, professional corporate photography, "
            "photorealistic, natural expressions, authentic business moment"
        ),
    },
    {
        "id": "B2",
        "filename": "luca_working_laptop.jpg",
        "use": "LinkedIn post, about section",
        "aspect_ratio": "4:3",
        "prompt": (
            f"{FACE_DESC}, "
            "sitting at a wooden cafe table working on a modern laptop, "
            "small espresso cup beside him, focused concentrated expression looking at screen, "
            "European cafe interior with large windows and natural light, "
            "warm cafe atmosphere with blurred background patrons, "
            "shot on Canon EOS R5, 50mm f/2 lens, natural window light, soft bokeh, "
            "photorealistic, candid lifestyle photography, slight warmth, Kodak Portra tones"
        ),
    },
    {
        "id": "B3",
        "filename": "luca_trade_fair.jpg",
        "use": "LinkedIn, Automechanika Frankfurt credibility",
        "aspect_ratio": "4:3",
        "prompt": (
            f"{FACE_DESC}, "
            "wearing navy blazer with a professional visitor badge on lanyard around neck, "
            "standing at a high table in a large automotive trade fair exhibition hall, "
            "trade fair booths and automotive displays visible in blurred background, "
            "bright overhead exhibition lighting, "
            "shot on Canon EOS R5, 35mm lens, f/4, event photography style, "
            "photorealistic, natural ambient light, slight noise, documentary feel"
        ),
    },
    {
        "id": "B4",
        "filename": "luca_phone_call.jpg",
        "use": "WA Day 10 vocal context, social 'always available'",
        "aspect_ratio": "3:4",
        "prompt": (
            f"{FACE_DESC}, "
            "holding a modern smartphone to his right ear in active conversation, "
            "relaxed focused expression with slight smile, standing in a bright hotel lobby, "
            "wearing dark navy blazer over white shirt, "
            "modern contemporary lobby interior with marble and glass, "
            "natural light from large entrance, "
            "shot on Canon EOS R5, 85mm f/1.8, shallow depth of field, "
            "photorealistic, candid moment, natural skin tones, professional"
        ),
    },

    # === CONTESTI EUROPEI (4) ===
    {
        "id": "E1",
        "filename": "luca_munich_street.jpg",
        "use": "LinkedIn 'da Monaco', backstory EU",
        "aspect_ratio": "4:3",
        "prompt": (
            f"{FACE_DESC}, "
            "walking on a Munich street, Marienplatz area architecture softly visible in background, "
            "wearing dark navy overcoat over blazer, carrying a dark leather messenger bag, "
            "autumn European weather, slightly overcast with warm spots of light, "
            "shot on Canon EOS R5, 35mm prime lens, f/2.8, street photography style, "
            "photorealistic, reportage feel, natural walking pose, slight motion, "
            "Kodak Portra 400 color tones, slight film grain"
        ),
    },
    {
        "id": "E2",
        "filename": "luca_port_logistics.jpg",
        "use": "Landing logistics section, import process",
        "aspect_ratio": "16:9",
        "prompt": (
            f"{FACE_DESC}, "
            "standing near a European commercial port area with car transport ship or vehicle storage visible, "
            "wearing navy blazer with dark trousers, hands in pockets, looking toward the port, "
            "industrial port infrastructure in background, cranes and cargo visible, "
            "overcast European sky, industrial yet clean setting, "
            "shot on Canon EOS R5, 24mm wide angle, f/5.6, "
            "photorealistic, documentary photography style, desaturated cool tones"
        ),
    },
    {
        "id": "E3",
        "filename": "luca_documents_review.jpg",
        "use": "Materiali formativi, dossier context",
        "aspect_ratio": "4:3",
        "prompt": (
            "Close-up of hands of a professional man reviewing printed vehicle documents "
            "and a laptop showing automotive listing screenshots, "
            "espresso cup on wooden table, reading glasses placed beside documents, "
            "European cafe or hotel lobby setting with warm natural light, "
            "papers show vehicle specifications and pricing data, "
            "shot on Canon EOS R5, 50mm macro, f/2.8, shallow depth of field, "
            "photorealistic, overhead slightly angled view, warm tones, "
            "professional working moment, detail-oriented"
        ),
    },
    {
        "id": "E4",
        "filename": "luca_car_transport.jpg",
        "use": "Import EU 6 Step transport section",
        "aspect_ratio": "16:9",
        "prompt": (
            f"{FACE_DESC}, "
            "standing near a car carrier truck (bisarca) loaded with premium vehicles including BMW and Mercedes, "
            "European highway rest area or logistics center, wearing navy blazer, "
            "observing the loaded vehicles with professional interest, "
            "partly cloudy European sky, industrial logistics setting, "
            "shot on Canon EOS R5, 35mm lens, f/4, wide scene, "
            "photorealistic, documentary reportage style, "
            "natural overcast lighting, authentic moment"
        ),
    },
]


def get_vertex_credentials():
    """Authenticate with Vertex AI service account"""
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request

    SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
    creds = service_account.Credentials.from_service_account_file(str(SA_PATH), scopes=SCOPES)
    creds.refresh(Request())
    return creds


def check_vertex_access():
    """Verify Vertex AI API is accessible and billing is active"""
    import requests
    creds = get_vertex_credentials()
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}

    # Test with a simple prompt
    model = "imagen-4.0-fast-generate-001"  # cheapest for test
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{model}:predict"
    payload = {
        "instances": [{"prompt": "A red apple on a white table, photorealistic"}],
        "parameters": {"sampleCount": 1, "aspectRatio": "1:1"}
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)

    if resp.status_code == 200:
        data = resp.json()
        if "predictions" in data and data["predictions"]:
            print(f"Vertex AI OK - Imagen accessible, billing active")
            print(f"Test image generated successfully")
            return True
    print(f"Vertex AI ERROR: {resp.status_code}")
    print(f"Response: {resp.text[:400]}")
    return False


def generate_image_vertex(prompt, output_path, model, aspect_ratio="1:1", seed=None):
    """Generate image via Vertex AI Imagen API"""
    import requests
    creds = get_vertex_credentials()
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}

    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{model}:predict"

    parameters = {
        "sampleCount": 1,
        "aspectRatio": aspect_ratio,
        "addWatermark": True,  # keep SynthID (legal compliance)
        "safetySetting": "block_few",  # permissive for business photos
        "personGeneration": "allow_all",  # enable person generation
    }

    # Add negative prompt
    if NEGATIVE_PROMPT:
        parameters["negativePrompt"] = NEGATIVE_PROMPT

    # Add seed for reproducibility if specified
    if seed is not None:
        parameters["seed"] = seed
        parameters["addWatermark"] = False  # required for seed to work

    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": parameters,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)

    if resp.status_code == 200:
        data = resp.json()
        if "predictions" in data and data["predictions"]:
            img_b64 = data["predictions"][0].get("bytesBase64Encoded", "")
            if img_b64:
                img_bytes = base64.b64decode(img_b64)
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                return True, len(img_bytes)
        return False, "No predictions in response"
    elif resp.status_code == 429:
        return False, "RATE_LIMITED"
    else:
        error_msg = resp.text[:300]
        return False, f"HTTP {resp.status_code}: {error_msg}"


def strip_exif_c2pa(filepath):
    """Remove EXIF and C2PA metadata (keeps SynthID which is pixel-embedded)"""
    try:
        # Remove all metadata but keep ICC color profile
        result = subprocess.run(
            ["exiftool", "-all=", "--icc_profile:all", "-overwrite_original", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        print("    WARNING: exiftool not installed. Metadata NOT stripped.")
        print("    Install: brew install exiftool")
    except Exception as e:
        print(f"    WARNING: exiftool error: {e}")
    return False


def visual_checklist(photo_id):
    """Print visual QA checklist (from research section 5.1)"""
    print(f"    QA CHECKLIST for {photo_id}:")
    print(f"    [ ] Hands: exactly 5 fingers per hand, no fusion")
    print(f"    [ ] Teeth: natural, not too white, not fused")
    print(f"    [ ] Eyes: consistent direction, natural reflections")
    print(f"    [ ] Skin: visible pores, no waxy/plastic zones")
    print(f"    [ ] Background: no repeating patterns, coherent architecture")
    print(f"    [ ] Clothing: real stitching, correct button count")


def main():
    check_only = "--check" in sys.argv
    use_fast = "--fast" in sys.argv
    variants_arg = 4  # default: 4 variants per photo

    for i, arg in enumerate(sys.argv):
        if arg == "--variants" and i + 1 < len(sys.argv):
            variants_arg = int(sys.argv[i + 1])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Model selection based on research:
    # Ultra: best for portraits ($0.06), Standard: good ($0.04), Fast: test ($0.02)
    if use_fast:
        model = "imagen-4.0-fast-generate-001"
        cost_per_img = 0.02
        print("Mode: Imagen 4 FAST (test quality, $0.02/img)")
    else:
        model = "imagen-4.0-ultra-generate-001"
        cost_per_img = 0.06
        print("Mode: Imagen 4 ULTRA (production quality, $0.06/img)")

    if check_only:
        print("\nChecking Vertex AI access...")
        ok = check_vertex_access()
        if ok:
            total_cost = len(PHOTO_SET) * variants_arg * cost_per_img
            print(f"\nReady to generate:")
            print(f"  Photos: {len(PHOTO_SET)}")
            print(f"  Variants per photo: {variants_arg}")
            print(f"  Total generations: {len(PHOTO_SET) * variants_arg}")
            print(f"  Estimated cost: ${total_cost:.2f}")
        return

    total_generations = len(PHOTO_SET) * variants_arg
    total_cost = total_generations * cost_per_img

    print("=" * 65)
    print("ARGOS — Generatore Immagini Luca Ferretti v2")
    print(f"Model: {model}")
    print(f"Photos: {len(PHOTO_SET)} | Variants: {variants_arg} | Total: {total_generations}")
    print(f"Estimated cost: ${total_cost:.2f} (covered by $300 free credits)")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 65)

    generated = 0
    skipped = 0
    failed = 0
    cost_spent = 0.0

    for i, photo in enumerate(PHOTO_SET, 1):
        pid = photo["id"]
        base_filename = photo["filename"]
        prompt = photo["prompt"]
        ar = photo["aspect_ratio"]
        use = photo["use"]

        print(f"\n[{i:2d}/15] {pid} — {base_filename}")
        print(f"  Use: {use}")
        print(f"  Aspect: {ar}")

        # Check if final (best) version exists
        final_path = OUTPUT_DIR / base_filename
        if final_path.exists() and final_path.stat().st_size > 50000:
            print(f"  SKIP (already exists, {final_path.stat().st_size // 1024}KB)")
            skipped += 1
            continue

        # Generate variants
        variant_paths = []
        for v in range(1, variants_arg + 1):
            variant_name = base_filename.replace(".jpg", f"_v{v}.jpg")
            variant_path = OUTPUT_DIR / variant_name

            if variant_path.exists() and variant_path.stat().st_size > 50000:
                print(f"  Variant {v}/{variants_arg}: EXISTS ({variant_path.stat().st_size // 1024}KB)")
                variant_paths.append(variant_path)
                continue

            print(f"  Variant {v}/{variants_arg}: generating...", end="", flush=True)

            ok, result = generate_image_vertex(prompt, variant_path, model, ar)

            if ok:
                stripped = strip_exif_c2pa(variant_path)
                meta_status = "EXIF stripped" if stripped else "EXIF kept"
                print(f" OK ({result // 1024}KB, {meta_status})")
                variant_paths.append(variant_path)
                cost_spent += cost_per_img
                generated += 1
            else:
                print(f" FAILED: {result}")
                failed += 1

                if result == "RATE_LIMITED":
                    print("  Waiting 30s for rate limit...")
                    time.sleep(30)
                    # Retry once
                    ok2, result2 = generate_image_vertex(prompt, variant_path, model, ar)
                    if ok2:
                        strip_exif_c2pa(variant_path)
                        print(f"  Retry OK ({result2 // 1024}KB)")
                        variant_paths.append(variant_path)
                        cost_spent += cost_per_img
                        generated += 1
                        failed -= 1

            # Rate limit: 3 sec between requests (research: 2 IPM for Tier 0)
            time.sleep(3)

        if variant_paths:
            # Copy first variant as the "best" (manual selection later)
            import shutil
            shutil.copy2(variant_paths[0], final_path)
            print(f"  Best (default v1): {final_path.name} ({final_path.stat().st_size // 1024}KB)")

            if variants_arg > 1:
                visual_checklist(pid)

        print(f"  Running cost: ${cost_spent:.2f}")

    # Summary
    print("\n" + "=" * 65)
    print("RISULTATO FINALE")
    print(f"  Generated: {generated}")
    print(f"  Skipped:   {skipped}")
    print(f"  Failed:    {failed}")
    print(f"  Cost:      ${cost_spent:.2f}")
    print(f"  Remaining credits: ~${300 - cost_spent:.2f}")
    print("=" * 65)

    if variants_arg > 1:
        print("\nPROSSIMO STEP:")
        print("  Apri la cartella e seleziona manualmente la MIGLIORE variante per ogni foto.")
        print(f"  Cartella: {OUTPUT_DIR}")
        print("  Rinomina la migliore come il nome base (es. luca_portrait_formal.jpg)")
        print("  Controlla la checklist QA per ogni foto selezionata.")

    # Save generation log
    log = {
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "model": model,
        "variants_per_photo": variants_arg,
        "generated": generated,
        "skipped": skipped,
        "failed": failed,
        "cost_usd": round(cost_spent, 2),
        "files": sorted([f for f in os.listdir(OUTPUT_DIR) if f.startswith("luca_")])
    }
    log_path = OUTPUT_DIR / "_generation_log.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"\nLog: {log_path}")


if __name__ == "__main__":
    main()

import serial, glob, os, time, threading
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from flask import Flask, render_template_string, send_from_directory
from flask_socketio import SocketIO

TRACK_CONFIG = {
    'TOUCH_1': {'name': 'Wire 1', 'color': '#ff4757', 'pin': 'D4', 'key': '1'},
    'TOUCH_2': {'name': 'Wire 2', 'color': '#ffa502', 'pin': 'D6', 'key': '2'},
    'TOUCH_3': {'name': 'Wire 3', 'color': '#2ed573', 'pin': 'D8', 'key': '3'},
    'TOUCH_4': {'name': 'Wire 4', 'color': '#1e90ff', 'pin': 'D10', 'key': '4'},
    'TOUCH_5': {'name': 'Wire 5', 'color': '#9b59b6', 'pin': 'D12', 'key': '5'},
    'TOUCH_6': {'name': 'Wire 6', 'color': '#e056fd', 'pin': 'D13', 'key': '6'}
}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'milkyway_orbital_starship_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

USER_HOME = os.path.expanduser('~')
POSSIBLE_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets'),
    os.path.join(USER_HOME, 'Downloads'),
    os.path.join(USER_HOME, 'Desktop')
]

@app.route('/duck_image')
def get_duck_image():
    for folder in POSSIBLE_PATHS:
        for fname in os.listdir(folder):
            if ('ChatGPT_Image' in fname or 'duck' in fname.lower()) and '01_48' in fname:
                if fname.endswith(('.svg', '.png', '.jpg', '.jpeg')):
                    return send_from_directory(folder, fname)
            elif 'duck' in fname.lower() and fname.endswith(('.svg', '.png', '.jpg', '.jpeg')):
                return send_from_directory(folder, fname)
    return "Duck image not found", 404

@app.route('/moon_image')
def get_moon_image():
    for folder in POSSIBLE_PATHS:
        for fname in os.listdir(folder):
            if ('ChatGPT_Image' in fname or 'moon' in fname.lower()) and '01_59' in fname:
                if fname.endswith(('.svg', '.png', '.jpg', '.jpeg')):
                    return send_from_directory(folder, fname)
            elif 'moon' in fname.lower() and fname.endswith(('.svg', '.png', '.jpg', '.jpeg')):
                return send_from_directory(folder, fname)
    return "Moon image not found", 404

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Space Ducky</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Press Start 2P', monospace; user-select: none; }
        html, body { width: 100%; height: 100%; background: #020208; color: #e0e0e0; overflow: hidden; }

        #game-container {
            position: relative;
            width: 100vw;
            height: 100vh;
            background: #020208;
            overflow: hidden;
        }

        canvas { display: block; image-rendering: pixelated; width: 100%; height: 100%; }

        .speed-hud-panel {
            background: rgba(19, 15, 38, 0.9);
            padding: 10px 18px;
            border: 4px solid #4834d4;
            font-size: 0.7rem;
            color: #c7ecee;
        }

        .ui-hud {
            position: absolute; top: 20px; left: 25px; right: 25px;
            display: flex; justify-content: space-between; align-items: flex-start;
            pointer-events: none;
            z-index: 5;
        }

        .score-box {
            font-size: 1.8rem;
            color: #00d2d3;
            letter-spacing: 2px;
            text-shadow: 2px 2px 0px #000;
            margin-bottom: 12px;
        }

        .hud-leaderboard {
            background: rgba(10, 9, 21, 0.88);
            border: 3px solid #6c5ce7;
            padding: 12px 14px;
            min-width: 260px;
            box-shadow: 4px 4px 0px #000;
        }

        .hud-lb-title {
            font-size: 0.65rem;
            color: #ffda79;
            margin-bottom: 8px;
            text-transform: uppercase;
            border-bottom: 2px solid #4834d4;
            padding-bottom: 4px;
        }

        .hud-lb-row {
            font-size: 0.55rem;
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            color: #c7ecee;
        }

        .hud-lb-row.active-pilot {
            color: #2ed573;
            font-weight: bold;
        }

        .hud-lb-row.done-player {
            color: #888888;
        }

        .wire-bar {
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            display: flex; gap: 10px; z-index: 10;
            transition: opacity 0.3s ease;
            max-width: 95vw;
            flex-wrap: wrap;
            justify-content: center;
        }

        .wire-card {
            background: #0e0d1a; padding: 8px 12px;
            border: 4px solid;
            font-size: 0.55rem; transition: all 0.1s ease;
        }

        .wire-card.active {
            background: #ffffff !important; color: #000000 !important; border-color: #ffffff !important;
            transform: translateY(-4px);
        }

        .overlay-screen {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(2, 2, 10, 0.92);
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            z-index: 20;
        }

        .dialogue-container {
            position: absolute;
            top: 50%;
            right: 10vw;
            transform: translateY(-50%);
            width: 48vw;
            max-width: 650px;
            background: #ffffff;
            color: #0f1026;
            padding: 32px 28px 24px 28px;
            z-index: 25;
            display: none;
            image-rendering: pixelated;
            
            box-shadow:
                0 -8px 0 0 #0f1026,
                0 8px 0 0 #0f1026,
                -8px 0 0 0 #0f1026,
                8px 0 0 0 #0f1026,
                -8px -8px 0 0 #0f1026,
                8px -8px 0 0 #0f1026,
                -8px 8px 0 0 #0f1026,
                8px 8px 0 0 #0f1026,
                0 16px 0 0 #81ecec,
                16px 0 0 0 #81ecec,
                16px 16px 0 0 #0f1026;
        }

        .dialogue-speaker {
            font-size: 0.8rem;
            color: #ffffff;
            background: #6c5ce7;
            padding: 6px 12px;
            display: inline-block;
            border: 3px solid #0f1026;
            margin-bottom: 16px;
            letter-spacing: 1px;
            box-shadow: 3px 3px 0px #0f1026;
        }

        .dialogue-text {
            font-size: 0.72rem;
            color: #0f1026;
            line-height: 1.9;
            min-height: 3.5em;
            letter-spacing: 0.5px;
            font-weight: bold;
        }

        .dialogue-prompt {
            font-size: 0.6rem;
            color: #10ac84;
            text-align: right;
            margin-top: 18px;
            font-weight: bold;
            animation: pulseCloudText 0.6s infinite steps(2, start);
        }

        @keyframes pulseCloudText {
            0% { opacity: 0.2; }
            100% { opacity: 1; }
        }

        .count-btn-group {
            display: flex; gap: 8px; margin-top: 15px; flex-wrap: wrap;
        }
        .btn-count {
            background: #6c5ce7; color: #fff; border: 3px solid #0f1026;
            padding: 8px 10px; font-size: 0.7rem; cursor: pointer;
            box-shadow: 3px 3px 0 #0f1026; font-family: 'Press Start 2P', monospace;
        }
        .btn-count:hover { background: #512da8; }

        .name-input-group {
            display: flex; flex-direction: column; gap: 8px; margin-top: 12px;
            max-height: 220px; overflow-y: auto; padding-right: 5px;
        }
        .player-input-row {
            display: flex; align-items: center; gap: 8px;
        }
        .player-input-row label {
            font-size: 0.6rem; color: #6c5ce7; width: 85px;
        }
        .player-input-row input {
            font-family: 'Press Start 2P', monospace;
            font-size: 0.6rem; padding: 5px 7px; border: 3px solid #0f1026;
            background: #f1f2f6; color: #0f1026; flex: 1; outline: none;
        }

        .wire-assignment-list {
            margin-top: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: #0f1026;
            padding: 12px;
            border: 3px solid #6c5ce7;
            max-height: 200px;
            overflow-y: auto;
        }

        .wire-assign-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.62rem;
            padding: 6px 8px;
            border-bottom: 1px dashed rgba(255,255,255,0.2);
        }

        .wire-badge {
            padding: 4px 6px;
            background: #ffffff;
            color: #0f1026;
            font-weight: bold;
            border-radius: 3px;
        }

        .btn-confirm-names {
            margin-top: 12px; background: #2ed573; color: #0f1026;
            border: 3px solid #0f1026; padding: 10px 14px; font-size: 0.65rem;
            cursor: pointer; box-shadow: 3px 3px 0 #0f1026; font-weight: bold;
            font-family: 'Press Start 2P', monospace; width: 100%;
        }
        .btn-confirm-names:hover { background: #26af5f; }

        .btn-restart {
            margin-top: 25px; padding: 16px 28px; font-size: 0.85rem;
            font-family: 'Press Start 2P', monospace; background: #ff4757;
            color: #ffffff; border: 4px solid #ffffff; cursor: pointer;
            box-shadow: 4px 4px 0px #000;
        }

        .btn-restart:active { transform: translate(2px, 2px); box-shadow: 2px 2px 0px #000; }

        .final-lb-card {
            background: #0f1026;
            border: 6px solid #e056fd;
            padding: 30px 40px;
            width: 80vw;
            max-width: 680px;
            box-shadow: 8px 8px 0px #000;
            text-align: center;
        }

        .final-lb-table {
            width: 100%;
            margin-top: 20px;
            border-collapse: collapse;
        }

        .final-lb-table th {
            font-size: 0.7rem;
            color: #ffda79;
            padding-bottom: 12px;
            border-bottom: 3px solid #4834d4;
        }

        .final-lb-table td {
            font-size: 0.75rem;
            padding: 12px 6px;
            color: #ffffff;
            border-bottom: 1px solid #222;
        }

        .winner-row td {
            color: #2ed573 !important;
            font-size: 0.85rem !important;
            font-weight: bold;
        }

        #red-alert-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(255, 0, 0, 0.35); pointer-events: none;
            z-index: 15; opacity: 0; transition: opacity 0.1s ease;
        }
    </style>
</head>
<body>

    <div id="game-container">
        <div id="red-alert-overlay"></div>

        <div class="ui-hud">
            <div>
                <div class="score-box">SCORE: <span id="score">0000</span></div>
                <div class="hud-leaderboard">
                    <div class="hud-lb-title">CREW LEADERBOARD</div>
                    <div id="hud-lb-list"></div>
                </div>
            </div>
            <div class="speed-hud-panel">
                TRACK LAYER: <span id="layerHud" style="color: #2ed573;">LOW SUB-BASS (INTRO)</span><br>
                SPEED: <span id="speedVal" style="color: #e056fd;">0.4x</span>
            </div>
        </div>

        <canvas id="gameCanvas"></canvas>

        <div id="start-screen" class="overlay-screen">
            <h1 style="font-size: 2rem; color: #e056fd; margin-bottom: 20px;">SPACE DUCKY</h1>
            <p id="start-prompt-text" style="font-size: 0.85rem; color: #c7ecee; line-height: 2;">TOUCH ANY WIRE TO BEGIN MISSION LOG</p>
        </div>

        <div id="dialogue-box" class="dialogue-container">
            <div class="dialogue-speaker">COMMANDER DUCKY</div>
            <div id="dialogue-content" class="dialogue-text"></div>
            <div id="dialogue-interactive-area"></div>
            <div id="dialogue-prompt" class="dialogue-prompt">[ TOUCH WIRE TO CONTINUE ]</div>
        </div>

        <div id="turn-screen" class="overlay-screen" style="display: none;">
            <h1 id="turn-title" style="font-size: 2rem; color: #ff4757; margin-bottom: 15px;">PILOT CRASHED!</h1>
            <p id="turn-score-text" style="font-size: 0.9rem; color: #ffbe76; margin-bottom: 25px;">SCORE: 0</p>
            <div style="background: #130f26; border: 4px solid #6c5ce7; padding: 20px 30px; text-align: center; margin-bottom: 25px;">
                <p style="font-size: 0.7rem; color: #aaa; margin-bottom: 10px;">NEXT PILOT UP:</p>
                <p id="next-pilot-name" style="font-size: 1.3rem; color: #2ed573;"></p>
            </div>
            <button class="btn-restart" onclick="startNextTurn()">TOUCH WIRE TO LAUNCH NEXT PILOT</button>
        </div>

        <div id="game-over-screen" class="overlay-screen" style="display: none;">
            <div class="final-lb-card">
                <h1 style="font-size: 1.8rem; color: #ffda79; margin-bottom: 10px;">MISSION COMPLETE!</h1>
                <p id="winner-announcement" style="font-size: 0.8rem; color: #2ed573; margin-bottom: 15px; line-height: 1.6;"></p>
                
                <table class="final-lb-table">
                    <thead>
                        <tr>
                            <th>RANK</th>
                            <th>PILOT</th>
                            <th>SCORE</th>
                        </tr>
                    </thead>
                    <tbody id="final-lb-body"></tbody>
                </table>

                <button class="btn-restart" onclick="resetToStart()">TOUCH WIRE TO PLAY NEW GAME</button>
            </div>
        </div>

        <div id="wire-bar-container" class="wire-bar"></div>
    </div>

    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const socket = io();

        /* --- AUDIO & CRASH SOUND FX ENGINE --- */
        let audioCtx = null;
        let isMusicPlaying = false;
        let musicLayerStep = 0;

        const LAYER_NAMES = [
            "INTRO (LOW SUB-BASS)",
            "LAYER 1: DEEP BASSLINE",
            "LAYER 2: DRUMS & PERC",
            "LAYER 3: SYNTH KEYS",
            "LAYER 4: LEAD MELODY",
            "LAYER 5: PIANO ARPS",
            "LAYER 6: FULL DROP (GUITAR/FX)"
        ];

        let gains = {
            intro: null,
            bass: null,
            drums: null,
            synth: null,
            lead: null,
            piano: null,
            guitar: null
        };

        const BPM = 142;
        const BEAT_TIME = 60 / BPM;
        let noteTick = 0;

        const LOW_SUB_NOTES = [87.31, 65.41, 98.00, 110.00];
        const BASS_NOTES = [174.61, 130.81, 196.00, 220.00];
        const SYNTH_CHORDS = [
            [349.23, 440.00, 523.25],
            [261.63, 329.63, 392.00],
            [293.66, 392.00, 493.88],
            [440.00, 523.25, 659.25]
        ];
        const LEAD_MELODY = [523.25, 587.33, 659.25, 783.99, 659.25, 587.33, 523.25, 440.00];
        const PIANO_ARPS = [1046.50, 880.00, 783.99, 659.25, 523.25, 659.25, 783.99, 880.00];

        function initAudioEngine() {
            if (audioCtx) {
                if (audioCtx.state === 'suspended') audioCtx.resume();
                return;
            }
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();

            /* LOWERED BACKGROUND MUSIC VOLUME GAINS */
            gains.intro = audioCtx.createGain(); gains.intro.gain.value = 0.25;
            gains.bass = audioCtx.createGain(); gains.bass.gain.value = 0;
            gains.drums = audioCtx.createGain(); gains.drums.gain.value = 0;
            gains.synth = audioCtx.createGain(); gains.synth.gain.value = 0;
            gains.lead = audioCtx.createGain(); gains.lead.gain.value = 0;
            gains.piano = audioCtx.createGain(); gains.piano.gain.value = 0;
            gains.guitar = audioCtx.createGain(); gains.guitar.gain.value = 0;

            Object.keys(gains).forEach(k => gains[k].connect(audioCtx.destination));

            startGlobalMusicLoop();
            isMusicPlaying = true;
        }

        function playCrashSound() {
            if (!audioCtx) return;
            const now = audioCtx.currentTime;

            const noiseBuffer = audioCtx.createBuffer(1, audioCtx.sampleRate * 0.8, audioCtx.sampleRate);
            const output = noiseBuffer.getChannelData(0);
            for (let i = 0; i < noiseBuffer.length; i++) {
                output[i] = Math.random() * 2 - 1;
            }
            const whiteNoise = audioCtx.createBufferSource();
            whiteNoise.buffer = noiseBuffer;

            const filter = audioCtx.createBiquadFilter();
            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(800, now);
            filter.frequency.exponentialRampToValueAtTime(30, now + 0.7);

            const crashGain = audioCtx.createGain();
            crashGain.gain.setValueAtTime(0.8, now);
            crashGain.gain.exponentialRampToValueAtTime(0.001, now + 0.75);

            whiteNoise.connect(filter);
            filter.connect(crashGain);
            crashGain.connect(audioCtx.destination);

            whiteNoise.start(now);

            const osc = audioCtx.createOscillator();
            const oscGain = audioCtx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(320, now);
            osc.frequency.exponentialRampToValueAtTime(40, now + 0.6);

            oscGain.gain.setValueAtTime(0.5, now);
            oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);

            osc.connect(oscGain);
            oscGain.connect(audioCtx.destination);

            osc.start(now);
            osc.stop(now + 0.65);
        }

        /* HIGH-VOLUME LOUD HAPTIC FEEDBACK SOUND CHIME */
        function playTouchHapticChime() {
            if (!audioCtx) return;
            const now = audioCtx.currentTime;
            
            // Primary high oscillator
            const osc = audioCtx.createOscillator();
            const g = audioCtx.createGain();
            osc.type = 'square';
            osc.frequency.setValueAtTime(1046.50, now); // High C6
            osc.frequency.exponentialRampToValueAtTime(2093.00, now + 0.18); // Punchy pitch ramp
            
            // Boosted gain (volume set high)
            g.gain.setValueAtTime(0.75, now);
            g.gain.exponentialRampToValueAtTime(0.001, now + 0.20);
            
            osc.connect(g);
            g.connect(audioCtx.destination);
            osc.start(now);
            osc.stop(now + 0.21);

            // Sub harmonic punch for tangible tactile feel
            const oscSub = audioCtx.createOscillator();
            const gSub = audioCtx.createGain();
            oscSub.type = 'triangle';
            oscSub.frequency.setValueAtTime(523.25, now);
            oscSub.frequency.exponentialRampToValueAtTime(1046.50, now + 0.15);
            
            gSub.gain.setValueAtTime(0.65, now);
            gSub.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
            
            oscSub.connect(gSub);
            gSub.connect(audioCtx.destination);
            oscSub.start(now);
            oscSub.stop(now + 0.19);
        }

        function startGlobalMusicLoop() {
            let nextNoteTime = audioCtx.currentTime;

            function scheduleLoop() {
                while (nextNoteTime < audioCtx.currentTime + 0.1) {
                    playLoopStep(noteTick, nextNoteTime);
                    nextNoteTime += BEAT_TIME / 4;
                    noteTick = (noteTick + 1) % 64;
                }
                setTimeout(scheduleLoop, 25);
            }
            scheduleLoop();
        }

        function playLoopStep(step, time) {
            const chordIdx = Math.floor(step / 16) % 4;
            const sub = step % 16;

            if (sub === 0) {
                let subOsc = audioCtx.createOscillator();
                let subGain = audioCtx.createGain();
                subOsc.type = 'sine';
                subOsc.frequency.setValueAtTime(LOW_SUB_NOTES[chordIdx], time);
                subGain.gain.setValueAtTime(0.20, time);
                subGain.gain.exponentialRampToValueAtTime(0.01, time + BEAT_TIME * 3.8);
                subOsc.connect(subGain);
                subGain.connect(gains.intro);
                subOsc.start(time); subOsc.stop(time + BEAT_TIME * 4);
            }

            if (sub % 4 === 0) {
                let bassOsc = audioCtx.createOscillator();
                let bassGain = audioCtx.createGain();
                bassOsc.type = 'sawtooth';
                bassOsc.frequency.setValueAtTime(BASS_NOTES[chordIdx] / 2, time);
                bassGain.gain.setValueAtTime(0.18, time);
                bassGain.gain.exponentialRampToValueAtTime(0.01, time + BEAT_TIME * 0.9);
                bassOsc.connect(bassGain);
                bassOsc.connect(gains.bass);
                bassOsc.start(time); bassOsc.stop(time + BEAT_TIME * 0.95);
            }

            if (sub % 4 === 0) {
                let kOsc = audioCtx.createOscillator();
                let kGain = audioCtx.createGain();
                kOsc.frequency.setValueAtTime(150, time);
                kOsc.frequency.exponentialRampToValueAtTime(0.01, time + 0.12);
                kGain.gain.setValueAtTime(0.25, time);
                kGain.gain.exponentialRampToValueAtTime(0.01, time + 0.12);
                kOsc.connect(kGain); kGain.connect(gains.drums);
                kOsc.start(time); kOsc.stop(time + 0.13);
            }
            if (sub % 8 === 4) {
                let nBuffer = audioCtx.createBuffer(1, audioCtx.sampleRate * 0.1, audioCtx.sampleRate);
                let data = nBuffer.getChannelData(0);
                for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
                let noise = audioCtx.createBufferSource();
                noise.buffer = nBuffer;
                let snGain = audioCtx.createGain();
                snGain.gain.setValueAtTime(0.15, time);
                snGain.gain.exponentialRampToValueAtTime(0.01, time + 0.1);
                noise.connect(snGain); snGain.connect(gains.drums);
                noise.start(time);
            }

            if (sub % 2 === 0) {
                SYNTH_CHORDS[chordIdx].forEach(freq => {
                    let osc = audioCtx.createOscillator();
                    let g = audioCtx.createGain();
                    osc.type = 'square';
                    osc.frequency.setValueAtTime(freq, time);
                    g.gain.setValueAtTime(0.04, time);
                    g.gain.exponentialRampToValueAtTime(0.001, time + BEAT_TIME * 0.45);
                    osc.connect(g); g.connect(gains.synth);
                    osc.start(time); osc.stop(time + BEAT_TIME * 0.48);
                });
            }

            if (sub % 2 === 0) {
                let melFreq = LEAD_MELODY[(step / 2) % LEAD_MELODY.length];
                let osc = audioCtx.createOscillator();
                let g = audioCtx.createGain();
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(melFreq, time);
                g.gain.setValueAtTime(0.08, time);
                g.gain.exponentialRampToValueAtTime(0.01, time + BEAT_TIME * 0.4);
                osc.connect(g); g.connect(gains.lead);
                osc.start(time); osc.stop(time + BEAT_TIME * 0.42);
            }

            let pianoFreq = PIANO_ARPS[step % PIANO_ARPS.length];
            let pOsc = audioCtx.createOscillator();
            let pGain = audioCtx.createGain();
            pOsc.type = 'triangle';
            pOsc.frequency.setValueAtTime(pianoFreq, time);
            pGain.gain.setValueAtTime(0.07, time);
            pGain.gain.exponentialRampToValueAtTime(0.001, time + 0.15);
            pOsc.connect(pGain); pGain.connect(gains.piano);
            pOsc.start(time); pOsc.stop(time + 0.16);

            if (sub % 4 === 2) {
                let gOsc = audioCtx.createOscillator();
                let gGain = audioCtx.createGain();
                gOsc.type = 'sawtooth';
                gOsc.frequency.setValueAtTime(LEAD_MELODY[chordIdx] * 2, time);
                gGain.gain.setValueAtTime(0.10, time);
                gGain.gain.exponentialRampToValueAtTime(0.001, time + 0.25);
                gOsc.connect(gGain); gGain.connect(gains.guitar);
                gOsc.start(time); gOsc.stop(time + 0.26);
            }
        }

        function advanceMusicLayer() {
            initAudioEngine();
            playTouchHapticChime();

            if (musicLayerStep < 6) {
                musicLayerStep++;
            }

            const now = audioCtx.currentTime;
            const fadeTime = 0.4;

            if (musicLayerStep >= 1) gains.bass.gain.linearRampToValueAtTime(0.55, now + fadeTime);
            if (musicLayerStep >= 2) gains.drums.gain.linearRampToValueAtTime(0.55, now + fadeTime);
            if (musicLayerStep >= 3) gains.synth.gain.linearRampToValueAtTime(0.55, now + fadeTime);
            if (musicLayerStep >= 4) gains.lead.gain.linearRampToValueAtTime(0.55, now + fadeTime);
            if (musicLayerStep >= 5) gains.piano.gain.linearRampToValueAtTime(0.55, now + fadeTime);
            if (musicLayerStep >= 6) gains.guitar.gain.linearRampToValueAtTime(0.55, now + fadeTime);

            document.getElementById('layerHud').innerText = LAYER_NAMES[musicLayerStep] || "FULL DROP";
        }

        function resetMusicTrackToStart() {
            if (!audioCtx) return;
            musicLayerStep = 0;
            const now = audioCtx.currentTime;
            
            Object.keys(gains).forEach(key => {
                if (key !== 'intro') {
                    gains[key].gain.cancelScheduledValues(now);
                    gains[key].gain.setValueAtTime(0, now);
                }
            });

            document.getElementById('layerHud').innerText = LAYER_NAMES[0];
        }

        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        const DEFAULT_COLORS = ['#ff4757', '#ffa502', '#2ed573', '#1e90ff', '#9b59b6', '#e056fd'];
        const DEFAULT_PINS = ['D4', 'D6', 'D8', 'D10', 'D12', 'D13'];
        const DEFAULT_KEYS = ['1', '2', '3', '4', '5', '6'];

        let score = 0;
        let gameState = 'START';
        let activeShield = null;
        let activeShieldTime = 0;
        let gates = [];
        let particles = [];
        let thrusterParticles = [];
        let explosionDebris = [];
        let shockwaves = [];
        let floatingTexts = [];
        let stars = [];
        let pixelNebulas = [];
        let ufos = [];
        let spawnTimer = 0;
        let nextSpawnInterval = 400;
        let baseSpeed = 0.4;
        let gameSpeed = 0.4;
        let maxSpeed = 3.5;
        let moonAngle = 0;

        let screenShakeTime = 0;
        let screenShakeIntensity = 0;

        let zoomFactor = 1.0;
        let targetZoom = 1.0;
        let offsetX = 0;
        let targetOffsetX = 0;

        let selectedPlayerCount = 1;
        let players = []; 
        let currentPilotIndex = 0;
        let chosenCharacterPlayer = "";
        let secondaryPlayers = [];

        const STORY_DIALOGUES = [
            "QUACK! Welcome aboard Pilots! Systems are online, but Sector 7 is under attack!",
            "How many brave space explorers are in your crew today? (Max 6)",
            "ENTER CREW NAMES",
            "ASSIGNING PILOTS...",
            "WIRE CONTROLS ASSIGNED!",
            "Invasive Alien Disruptors are jamming our thrusters! Touch your assigned WIRE frequency when approaching an alien to activate shield protection!"
        ];
        let currentDialogueIdx = 0;

        const duckImage = new Image();
        duckImage.src = '/duck_image';

        const moonImage = new Image();
        moonImage.src = '/moon_image';

        const ALIEN_GRID = [
            [0,0,0,0,1,1,1,1,0,0,0,0],
            [0,0,0,1,1,1,1,1,1,0,0,0],
            [0,0,1,1,2,2,2,2,1,1,0,0],
            [0,1,1,2,2,3,2,2,2,1,1,0],
            [1,1,2,2,2,4,4,2,2,2,1,1],
            [1,1,2,3,3,4,4,3,3,2,1,1],
            [1,1,1,2,2,4,4,2,2,1,1,1],
            [0,1,1,1,1,4,4,1,1,1,1,0],
            [0,0,0,0,1,1,1,1,0,0,0,0],
            [0,1,1,0,1,0,0,1,0,1,1,0],
            [1,1,0,1,1,0,0,1,1,0,1,1],
            [1,0,0,1,0,0,0,0,1,0,0,1],
            [1,0,0,4,0,4,4,0,4,0,0,1]
        ];

        for (let i = 0; i < 140; i++) {
            stars.push({
                x: Math.random() * window.innerWidth,
                y: Math.random() * window.innerHeight,
                size: Math.random() > 0.8 ? 4 : Math.random() > 0.5 ? 2 : 1,
                speed: Math.random() * 0.5 + 0.1,
                alpha: Math.random() * 0.7 + 0.3
            });
        }

        for (let i = 0; i < 5; i++) {
            const clusterColor = ['#4834d4', '#be2edd', '#e056fd', '#30336b', '#192a56'][i % 5];
            const blocks = [];
            const centerCX = Math.random() * window.innerWidth;
            const centerCY = Math.random() * (window.innerHeight * 0.6);
            const blockSize = 12;

            for (let bx = -8; bx <= 8; bx++) {
                for (let by = -8; by <= 8; by++) {
                    const dist = Math.sqrt(bx*bx + by*by);
                    if (dist < 8 && Math.random() > dist * 0.1) {
                        blocks.push({
                            rx: bx * blockSize,
                            ry: by * blockSize,
                            alpha: Math.max(0.1, (1 - dist / 8) * (Math.random() * 0.5 + 0.3))
                        });
                    }
                }
            }

            pixelNebulas.push({
                x: centerCX, y: centerCY, color: clusterColor, speed: (i + 1) * 0.05, blocks: blocks
            });
        }

        for (let i = 0; i < 4; i++) {
            ufos.push({
                x: Math.random() * window.innerWidth,
                y: Math.random() * (window.innerHeight * 0.25),
                speed: Math.random() * 0.8 + 0.2,
                bobFreq: Math.random() * 0.05 + 0.02,
                size: Math.random() * 20 + 25,
                color: ['#2ed573', '#00d2d3', '#ff4757', '#e056fd'][i % 4]
            });
        }

        function updateWireBarUI() {
            const container = document.getElementById('wire-bar-container');
            container.innerHTML = '';

            if (secondaryPlayers.length === 0) {
                const defaultTracks = [
                    { id: 'TOUCH_1', key: '1', pin: 'D4', name: 'Wire 1', color: '#ff4757' },
                    { id: 'TOUCH_2', key: '2', pin: 'D6', name: 'Wire 2', color: '#ffa502' },
                    { id: 'TOUCH_3', key: '3', pin: 'D8', name: 'Wire 3', color: '#2ed573' },
                    { id: 'TOUCH_4', key: '4', pin: 'D10', name: 'Wire 4', color: '#1e90ff' },
                    { id: 'TOUCH_5', key: '5', pin: 'D12', name: 'Wire 5', color: '#9b59b6' },
                    { id: 'TOUCH_6', key: '6', pin: 'D13', name: 'Wire 6', color: '#e056fd' }
                ];
                defaultTracks.forEach(t => {
                    container.innerHTML += `<div id="card-${t.id}" class="wire-card" style="border-color: ${t.color}; color: ${t.color};">[${t.key}] ${t.pin}</div>`;
                });
            } else {
                secondaryPlayers.forEach(sp => {
                    container.innerHTML += `<div id="card-${sp.id}" class="wire-card" style="border-color: ${sp.color}; color: ${sp.color};">[${sp.key}] ${sp.pin} - ${sp.name}</div>`;
                });
            }
        }

        function updateHUDLeaderboard() {
            const lbContainer = document.getElementById('hud-lb-list');
            lbContainer.innerHTML = '';

            players.forEach((p, idx) => {
                let statusClass = '';
                let statusText = `${p.score} PTS`;
                
                if (idx === currentPilotIndex) {
                    statusClass = 'active-pilot';
                    statusText = '★ PILOT';
                } else if (p.played) {
                    statusClass = 'done-player';
                }

                lbContainer.innerHTML += `
                    <div class="hud-lb-row ${statusClass}">
                        <span>${p.name.toUpperCase()}</span>
                        <span>${statusText}</span>
                    </div>
                `;
            });
        }

        function setupPlayers(names) {
            players = names.map((n, idx) => ({
                name: n.trim() || `Player ${idx + 1}`,
                score: 0,
                played: false
            }));

            players.sort(() => Math.random() - 0.5);
            currentPilotIndex = 0;
            assignCurrentPilot();
        }

        function assignCurrentPilot() {
            const activePilotObj = players[currentPilotIndex];
            chosenCharacterPlayer = activePilotObj.name;

            secondaryPlayers = [];
            let colorIdx = 0;

            players.forEach((p) => {
                if (p.name !== chosenCharacterPlayer) {
                    secondaryPlayers.push({
                        id: `TOUCH_${colorIdx + 1}`,
                        key: DEFAULT_KEYS[colorIdx],
                        pin: DEFAULT_PINS[colorIdx],
                        name: p.name,
                        color: DEFAULT_COLORS[colorIdx]
                    });
                    colorIdx++;
                }
            });

            if (players.length === 1) {
                secondaryPlayers = [];
            }

            updateWireBarUI();
            updateHUDLeaderboard();
        }

        function spawnGate() {
            let activePool = secondaryPlayers;
            if (activePool.length === 0) {
                activePool = [
                    { id: 'TOUCH_1', pin: 'D4', name: 'WIRE 1', color: '#ff4757' },
                    { id: 'TOUCH_2', pin: 'D6', name: 'WIRE 2', color: '#ffa502' },
                    { id: 'TOUCH_3', pin: 'D8', name: 'WIRE 3', color: '#2ed573' },
                    { id: 'TOUCH_4', pin: 'D10', name: 'WIRE 4', color: '#1e90ff' },
                    { id: 'TOUCH_5', pin: 'D12', name: 'WIRE 5', color: '#9b59b6' },
                    { id: 'TOUCH_6', pin: 'D13', name: 'WIRE 6', color: '#e056fd' }
                ];
            }

            const randomGate = activePool[Math.floor(Math.random() * activePool.length)];
            gates.push({
                angle: -Math.PI / 2 + 1.8,
                height: 120,
                gateInfo: randomGate,
                passed: false
            });

            const baseInterval = Math.floor(180 / gameSpeed);
            nextSpawnInterval = baseInterval + Math.floor(Math.random() * (120 / gameSpeed));
        }

        function createParticles(x, y, color) {
            for (let i = 0; i < 22; i++) {
                particles.push({
                    x: x, y: y,
                    vx: (Math.random() - 0.5) * 8, vy: (Math.random() - 0.5) * 8,
                    size: Math.random() * 5 + 2, color: color, life: 1.0
                });
            }
        }

        function triggerDramaticExplosion(x, y) {
            screenShakeTime = 25;
            screenShakeIntensity = 18;

            playCrashSound();

            const alertElem = document.getElementById('red-alert-overlay');
            alertElem.style.opacity = '1';
            setTimeout(() => { alertElem.style.opacity = '0'; }, 150);

            shockwaves.push({ x: x, y: y, radius: 10, maxRadius: 350, alpha: 1.0, color: '#ff4757' });
            shockwaves.push({ x: x, y: y, radius: 5, maxRadius: 280, alpha: 1.0, color: '#ffa502' });

            const debrisColors = ['#ff4757', '#ffa502', '#ffda79', '#ffffff', '#222'];
            for (let i = 0; i < 65; i++) {
                const angle = Math.random() * Math.PI * 2;
                const speed = Math.random() * 16 + 4;
                explosionDebris.push({
                    x: x, y: y,
                    vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
                    size: Math.random() * 8 + 4,
                    color: debrisColors[Math.floor(Math.random() * debrisColors.length)],
                    life: 1.0, decay: Math.random() * 0.02 + 0.015
                });
            }
        }

        function renderDialogueStep() {
            const textElem = document.getElementById('dialogue-content');
            const interactiveElem = document.getElementById('dialogue-interactive-area');
            const promptElem = document.getElementById('dialogue-prompt');

            interactiveElem.innerHTML = '';
            promptElem.style.display = 'block';

            if (currentDialogueIdx === 1) {
                textElem.innerText = STORY_DIALOGUES[currentDialogueIdx];
                promptElem.style.display = 'none';

                let buttonsHTML = '<div class="count-btn-group">';
                for (let i = 1; i <= 6; i++) {
                    buttonsHTML += `<button class="btn-count" onclick="selectPlayerCount(${i})">${i} PLAYER${i > 1 ? 'S' : ''}</button>`;
                }
                buttonsHTML += '</div>';
                interactiveElem.innerHTML = buttonsHTML;

            } else if (currentDialogueIdx === 2) {
                textElem.innerText = `Great! Enter names for ${selectedPlayerCount} player(s):`;
                promptElem.style.display = 'none';

                let inputsHTML = '<div class="name-input-group">';
                for (let i = 1; i <= selectedPlayerCount; i++) {
                    inputsHTML += `
                        <div class="player-input-row">
                            <label>P${i} NAME:</label>
                            <input type="text" id="pname-${i}" value="Player ${i}" maxlength="12" />
                        </div>`;
                }
                inputsHTML += `</div><button class="btn-confirm-names" onclick="confirmNames()">CONFIRM CREW</button>`;
                interactiveElem.innerHTML = inputsHTML;

            } else if (currentDialogueIdx === 3) {
                textElem.innerText = `QUACK! Randomizing turn order...\n\n FIRST PILOT: ${chosenCharacterPlayer.toUpperCase()}!`;
            } else if (currentDialogueIdx === 4) {
                textElem.innerText = `WIRE HARDWARE ASSIGNMENTS:`;

                let assignHTML = '<div class="wire-assignment-list">';
                
                if (players.length === 1) {
                    assignHTML += `
                        <div class="wire-assign-row">
                            <span style="color: #2ed573;">${players[0].name.toUpperCase()} (SOLO PILOT)</span>
                            <span class="wire-badge">ANY WIRE / KEY 1-6</span>
                        </div>
                    `;
                } else {
                    players.forEach((p, idx) => {
                        const pin = DEFAULT_PINS[idx % DEFAULT_PINS.length];
                        const key = DEFAULT_KEYS[idx % DEFAULT_KEYS.length];
                        const color = DEFAULT_COLORS[idx % DEFAULT_COLORS.length];

                        assignHTML += `
                            <div class="wire-assign-row">
                                <span style="color: ${color};">${p.name.toUpperCase()}</span>
                                <span class="wire-badge" style="border: 2px solid ${color};">PIN ${pin} [KEY ${key}]</span>
                            </div>
                        `;
                    });
                }

                assignHTML += '</div>';
                interactiveElem.innerHTML = assignHTML;
            } else {
                textElem.innerText = STORY_DIALOGUES[currentDialogueIdx];
            }
        }

        function selectPlayerCount(count) {
            advanceMusicLayer();
            selectedPlayerCount = count;
            currentDialogueIdx = 2;
            renderDialogueStep();
        }

        function confirmNames() {
            advanceMusicLayer();
            let names = [];
            for (let i = 1; i <= selectedPlayerCount; i++) {
                const val = document.getElementById(`pname-${i}`).value;
                names.push(val);
            }
            setupPlayers(names);
            currentDialogueIdx = 3;
            renderDialogueStep();
        }

        function handleTouchTrigger(triggerId) {
            advanceMusicLayer();

            if (gameState === 'PLAYING') {
                if (secondaryPlayers.length > 0) {
                    const isWireActivePlayer = secondaryPlayers.some(p => p.id === triggerId);
                    if (!isWireActivePlayer) return;
                }
            }

            const card = document.getElementById('card-' + triggerId);
            if (card) {
                card.classList.add('active');
                setTimeout(() => card.classList.remove('active'), 400);
            }

            if (gameState === 'START') {
                gameState = 'STORY';
                document.getElementById('start-screen').style.display = 'none';
                document.getElementById('dialogue-box').style.display = 'block';
                document.getElementById('wire-bar-container').style.display = 'none';
                targetZoom = 6.5;
                targetOffsetX = canvas.width * 0.22;
                currentDialogueIdx = 0;
                renderDialogueStep();
                return;
            }

            if (gameState === 'STORY') {
                if (currentDialogueIdx === 1 || currentDialogueIdx === 2) return;

                currentDialogueIdx++;
                if (currentDialogueIdx < STORY_DIALOGUES.length) {
                    renderDialogueStep();
                } else {
                    gameState = 'READY_TO_PLAY';
                    document.getElementById('dialogue-box').style.display = 'none';
                    document.getElementById('start-screen').style.display = 'flex';
                    document.getElementById('start-prompt-text').innerText = "TOUCH ANY WIRE TO START THE GAME";
                    document.getElementById('wire-bar-container').style.display = 'flex';
                    
                    targetZoom = 1.0;
                    targetOffsetX = 0;
                }
                return;
            }

            if (gameState === 'READY_TO_PLAY') {
                startGame();
                return;
            }

            if (gameState === 'TURN_TRANSITION') {
                startNextTurn();
                return;
            }

            if (gameState === 'GAMEOVER') {
                resetToStart();
                return;
            }

            if (gameState === 'PLAYING') {
                activeShield = triggerId;
                activeShieldTime = Date.now();
            }
        }

        socket.on('update_stem', function(data) {
            handleTouchTrigger(data.trigger);
        });

        window.addEventListener('keydown', (e) => {
            if (['1', '2', '3', '4', '5', '6'].includes(e.key)) handleTouchTrigger('TOUCH_' + e.key);
        });

        function handlePlayerDeath() {
            players[currentPilotIndex].score = score;
            players[currentPilotIndex].played = true;

            currentPilotIndex++;
            resetMusicTrackToStart();

            if (currentPilotIndex < players.length) {
                gameState = 'TURN_TRANSITION';
                document.getElementById('turn-title').innerText = `${players[currentPilotIndex - 1].name.toUpperCase()} CRASHED!`;
                document.getElementById('turn-score-text').innerText = `SCORE: ${score}`;
                document.getElementById('next-pilot-name').innerText = players[currentPilotIndex].name.toUpperCase();
                
                setTimeout(() => {
                    document.getElementById('turn-screen').style.display = 'flex';
                }, 800);
            } else {
                gameState = 'GAMEOVER';
                showFinalLeaderboard();
            }
        }

        function startNextTurn() {
            document.getElementById('turn-screen').style.display = 'none';
            resetMusicTrackToStart();
            assignCurrentPilot();
            startGame();
        }

        function showFinalLeaderboard() {
            const sorted = [...players].sort((a, b) => b.score - a.score);
            const winner = sorted[0];

            document.getElementById('winner-announcement').innerHTML = 
                `🏆 VICTORY TO <strong>${winner.name.toUpperCase()}</strong>! 🏆<br>HIGHEST SCORE: ${winner.score} PTS`;

            const tbody = document.getElementById('final-lb-body');
            tbody.innerHTML = '';

            sorted.forEach((p, idx) => {
                const rankStr = idx === 0 ? '🥇 1ST' : idx === 1 ? '🥈 2ND' : idx === 2 ? '🥉 3RD' : `${idx + 1}TH`;
                const isWinnerRow = idx === 0 ? 'class="winner-row"' : '';

                tbody.innerHTML += `
                    <tr ${isWinnerRow}>
                        <td>${rankStr}</td>
                        <td>${p.name.toUpperCase()}</td>
                        <td>${p.score}</td>
                    </tr>
                `;
            });

            setTimeout(() => {
                document.getElementById('game-over-screen').style.display = 'flex';
            }, 800);
        }

        function resetToStart() {
            gameState = 'START';
            targetZoom = 1.0;
            targetOffsetX = 0;
            resetMusicTrackToStart();
            document.getElementById('game-over-screen').style.display = 'none';
            document.getElementById('turn-screen').style.display = 'none';
            document.getElementById('dialogue-box').style.display = 'none';
            document.getElementById('wire-bar-container').style.display = 'flex';
            document.getElementById('start-screen').style.display = 'flex';
            document.getElementById('start-prompt-text').innerText = "TOUCH ANY WIRE TO BEGIN MISSION LOG";
        }

        function startGame() {
            score = 0;
            gameSpeed = baseSpeed;
            gates = [];
            particles = [];
            thrusterParticles = [];
            explosionDebris = [];
            shockwaves = [];
            floatingTexts = [];
            spawnTimer = 0;
            gameState = 'PLAYING';
            targetZoom = 1.0;
            targetOffsetX = 0;
            document.getElementById('start-screen').style.display = 'none';
            document.getElementById('game-over-screen').style.display = 'none';
            document.getElementById('turn-screen').style.display = 'none';
            document.getElementById('dialogue-box').style.display = 'none';
            document.getElementById('wire-bar-container').style.display = 'flex';
            document.getElementById('score').innerText = '0000';
            document.getElementById('speedVal').innerText = gameSpeed.toFixed(1) + 'x';
            updateHUDLeaderboard();
        }

        function drawPixelatedGalaxyBackground() {
            ctx.fillStyle = '#02020a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            pixelNebulas.forEach(pn => {
                ctx.fillStyle = pn.color;
                pn.blocks.forEach(b => {
                    ctx.globalAlpha = b.alpha;
                    ctx.fillRect(Math.floor(pn.x + b.rx), Math.floor(pn.y + b.ry), 12, 12);
                });
                ctx.globalAlpha = 1.0;

                if (gameState === 'PLAYING') {
                    pn.x -= pn.speed * gameSpeed;
                    if (pn.x < -200) pn.x = canvas.width + 200;
                }
            });

            stars.forEach(s => {
                ctx.fillStyle = '#ffffff';
                ctx.globalAlpha = s.alpha;
                ctx.fillRect(Math.floor(s.x), Math.floor(s.y), s.size, s.size);
                ctx.globalAlpha = 1.0;

                if (gameState === 'PLAYING') {
                    s.x -= s.speed * gameSpeed;
                    if (s.x < 0) s.x = canvas.width;
                }
            });

            ufos.forEach(u => {
                u.x -= u.speed * (gameState === 'PLAYING' ? gameSpeed : 0.2);
                if (u.x < -100) u.x = canvas.width + 100;

                const ufoY = u.y + Math.sin(Date.now() * 0.003 * u.bobFreq) * 12;

                ctx.fillStyle = '#00d2d3';
                ctx.fillRect(Math.floor(u.x - u.size * 0.2), Math.floor(ufoY - 6), Math.floor(u.size * 0.4), 6);

                ctx.fillStyle = u.color;
                ctx.fillRect(Math.floor(u.x - u.size * 0.5), Math.floor(ufoY), Math.floor(u.size), 8);
            });
        }

        function drawRotatingMoon(moonX, moonY, moonRadius) {
            ctx.save();
            ctx.translate(moonX, moonY);
            ctx.rotate(moonAngle);
            ctx.imageSmoothingEnabled = false;

            const moonDiameter = moonRadius * 2;
            ctx.drawImage(moonImage, -moonRadius, -moonRadius, moonDiameter, moonDiameter);

            ctx.restore();
        }

        function drawExactAlienMonster(primaryColor, labelName) {
            ctx.save();
            const px = 8.0;
            const cols = 12;
            const rows = 13;
            const totalW = cols * px;
            const totalH = rows * px;

            ctx.translate(-totalW / 2, -totalH / 2);

            ctx.save();
            ctx.shadowColor = primaryColor;
            ctx.shadowBlur = 20;
            ctx.fillStyle = primaryColor;
            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    if (ALIEN_GRID[r][c] !== 0) ctx.fillRect(c * px, r * px, px, px);
                }
            }
            ctx.restore();

            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    const val = ALIEN_GRID[r][c];
                    if (val === 0) continue;

                    if (val === 1) ctx.fillStyle = primaryColor;
                    else if (val === 2) ctx.fillStyle = '#ffffff';
                    else if (val === 3) ctx.fillStyle = '#0a0915';
                    else if (val === 4) ctx.fillStyle = '#ffea00';

                    ctx.fillRect(c * px, r * px, px, px);
                    ctx.strokeStyle = 'rgba(0,0,0,0.3)';
                    ctx.lineWidth = 0.5;
                    ctx.strokeRect(c * px, r * px, px, px);
                }
            }
            ctx.restore();

            ctx.save();
            ctx.fillStyle = '#ffffff';
            ctx.font = '11px "Press Start 2P"';
            ctx.textAlign = 'center';
            ctx.shadowColor = primaryColor;
            ctx.shadowBlur = 10;
            ctx.fillText(labelName, 0, -totalH / 2 - 14);
            ctx.restore();
        }

        function update() {
            ctx.save();

            const lerpSpeed = 0.045;
            zoomFactor += (targetZoom - zoomFactor) * lerpSpeed;
            offsetX += (targetOffsetX - offsetX) * lerpSpeed;

            const moonRadius = canvas.height * 0.85;
            const moonX = canvas.width / 2;
            const moonY = canvas.height + moonRadius * 0.40;

            const playerAngle = -Math.PI / 2;
            const duckHoverDist = moonRadius + 15;
            const playerX = moonX + Math.cos(playerAngle) * duckHoverDist;
            const playerY = moonY + Math.sin(playerAngle) * duckHoverDist;

            if (Math.abs(zoomFactor - 1.0) > 0.005 || Math.abs(offsetX) > 0.5) {
                ctx.translate(canvas.width / 2 - offsetX, canvas.height / 2);
                ctx.scale(zoomFactor, zoomFactor);
                ctx.translate(-playerX, -playerY + 28);
            }

            if (screenShakeTime > 0) {
                const sx = (Math.random() - 0.5) * screenShakeIntensity;
                const sy = (Math.random() - 0.5) * screenShakeIntensity;
                ctx.translate(sx, sy);
                screenShakeTime--;
            }

            drawPixelatedGalaxyBackground();

            if (gameState === 'PLAYING') {
                if (gameSpeed < maxSpeed) {
                    gameSpeed += 0.00015;
                    document.getElementById('speedVal').innerText = gameSpeed.toFixed(1) + 'x';
                }
                moonAngle -= 0.006 * gameSpeed;
            }

            drawRotatingMoon(moonX, moonY, moonRadius);

            if (gameState === 'PLAYING' && Math.random() < 0.8) {
                thrusterParticles.push({
                    x: playerX - 45,
                    y: playerY + 10 + (Math.random() - 0.5) * 10,
                    vx: -gameSpeed * 4 - Math.random() * 2,
                    vy: (Math.random() - 0.5) * 1.5,
                    size: Math.random() * 5 + 3,
                    color: Math.random() > 0.5 ? '#e056fd' : '#00d2d3',
                    life: 1.0
                });
            }

            for (let i = thrusterParticles.length - 1; i >= 0; i--) {
                let tp = thrusterParticles[i];
                tp.x += tp.vx; tp.y += tp.vy; tp.life -= 0.04;
                ctx.fillStyle = tp.color;
                ctx.globalAlpha = Math.max(0, tp.life);
                ctx.fillRect(tp.x, tp.y, tp.size, tp.size);
                ctx.globalAlpha = 1.0;
                if (tp.life <= 0) thrusterParticles.splice(i, 1);
            }

            if (gameState !== 'GAMEOVER' && gameState !== 'TURN_TRANSITION') {
                ctx.save();
                ctx.translate(playerX, playerY);

                if (activeShield && (Date.now() - activeShieldTime < 2500)) {
                    let shieldColor = '#ffffff';
                    const activeMatch = secondaryPlayers.find(g => g.id === activeShield);
                    if (activeMatch) shieldColor = activeMatch.color;

                    ctx.strokeStyle = shieldColor;
                    ctx.lineWidth = 5;
                    ctx.shadowColor = shieldColor;
                    ctx.shadowBlur = 25;
                    ctx.beginPath();
                    ctx.arc(0, 0, 65, 0, Math.PI * 2);
                    ctx.stroke();
                    ctx.shadowBlur = 0;
                }

                const duckSize = 130;
                ctx.imageSmoothingEnabled = false;
                ctx.drawImage(duckImage, -duckSize / 2, -duckSize / 2, duckSize, duckSize);

                if (gameState === 'PLAYING' && chosenCharacterPlayer) {
                    ctx.fillStyle = '#ffda79';
                    ctx.font = '12px "Press Start 2P"';
                    ctx.textAlign = 'center';
                    ctx.shadowColor = '#000000';
                    ctx.shadowBlur = 8;
                    ctx.fillText(chosenCharacterPlayer.toUpperCase(), 0, -duckSize / 2 - 12);
                }

                ctx.restore();
            }

            if (gameState === 'PLAYING') {
                spawnTimer++;
                if (spawnTimer >= nextSpawnInterval) {
                    spawnGate();
                    spawnTimer = 0;
                }

                for (let i = gates.length - 1; i >= 0; i--) {
                    let g = gates[i];
                    g.angle -= 0.006 * gameSpeed;

                    const currAngle = g.angle;
                    const obstacleRadius = moonRadius + 22;
                    const gx = moonX + Math.cos(currAngle) * obstacleRadius;
                    const gy = moonY + Math.sin(currAngle) * obstacleRadius;

                    ctx.save();
                    ctx.translate(gx, gy);
                    ctx.rotate(currAngle + Math.PI / 2);
                    drawExactAlienMonster(g.gateInfo.color, g.gateInfo.name.toUpperCase());
                    ctx.restore();

                    const angleDiff = Math.abs(currAngle - playerAngle);
                    if (angleDiff < 0.075 && !g.passed) {
                        const shieldValid = activeShield === g.gateInfo.id && (Date.now() - activeShieldTime < 2500);
                        if (shieldValid) {
                            g.passed = true;
                            score += 10;
                            document.getElementById('score').innerText = String(score).padStart(4, '0');
                            createParticles(gx, gy, g.gateInfo.color);

                            floatingTexts.push({
                                x: playerX - 40, y: playerY - 70,
                                text: '+10 SCORE', color: g.gateInfo.color, life: 1.0
                            });
                        } else {
                            triggerDramaticExplosion(playerX, playerY);
                            handlePlayerDeath();
                        }
                    }

                    if (currAngle < -Math.PI) gates.splice(i, 1);
                }
            }

            for (let i = shockwaves.length - 1; i >= 0; i--) {
                let sw = shockwaves[i];
                sw.radius += 12;
                sw.alpha -= 0.025;
                ctx.strokeStyle = sw.color;
                ctx.lineWidth = 6;
                ctx.globalAlpha = Math.max(0, sw.alpha);
                ctx.beginPath();
                ctx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
                ctx.stroke();
                ctx.globalAlpha = 1.0;
                if (sw.alpha <= 0) shockwaves.splice(i, 1);
            }

            for (let i = explosionDebris.length - 1; i >= 0; i--) {
                let ed = explosionDebris[i];
                ed.x += ed.vx; ed.y += ed.vy; ed.life -= ed.decay;
                ctx.fillStyle = ed.color;
                ctx.globalAlpha = Math.max(0, ed.life);
                ctx.fillRect(ed.x, ed.y, ed.size, ed.size);
                ctx.globalAlpha = 1.0;
                if (ed.life <= 0) explosionDebris.splice(i, 1);
            }

            for (let i = particles.length - 1; i >= 0; i--) {
                let p = particles[i];
                p.x += p.vx; p.y += p.vy; p.life -= 0.02;
                ctx.fillStyle = p.color;
                ctx.globalAlpha = Math.max(0, p.life);
                ctx.fillRect(p.x, p.y, p.size, p.size);
                ctx.globalAlpha = 1.0;
                if (p.life <= 0) particles.splice(i, 1);
            }

            for (let i = floatingTexts.length - 1; i >= 0; i--) {
                let ft = floatingTexts[i];
                ft.y -= 0.8; ft.life -= 0.02;
                ctx.fillStyle = ft.color;
                ctx.globalAlpha = Math.max(0, ft.life);
                ctx.font = '10px "Press Start 2P"';
                ctx.fillText(ft.text, ft.x, ft.y);
                ctx.globalAlpha = 1.0;
                if (ft.life <= 0) floatingTexts.splice(i, 1);
            }

            ctx.restore();
        }

        updateWireBarUI();
        setInterval(update, 1000 / 60);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, tracks=TRACK_CONFIG)

def run_touch_system():
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.init()

    ports = glob.glob('/dev/cu.usbserial*') + glob.glob('/dev/cu.usbmodem*')
    if not ports:
        print('\n[ERROR] No Arduino found! Check USB connection.')
        return

    port = ports[0]
    print(f'\n[CONNECTED] Serial port: {port} at 230400 baud')
    print('[GAME READY] Open Space Ducky at: http://localhost:5001\n')

    ser = serial.Serial(port, 230400, timeout=0.001)
    last_trigger_times = {}

    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line in TRACK_CONFIG:
                    now = time.time()
                    if line in last_trigger_times and (now - last_trigger_times[line]) < 0.3:
                        continue
                    last_trigger_times[line] = now

                    socketio.emit('update_stem', {'trigger': line})
            time.sleep(0.005)
        except Exception:
            pass

if __name__ == '__main__':
    t = threading.Thread(target=run_touch_system, daemon=True)
    t.start()
    socketio.run(app, host='127.0.0.1', port=5001, allow_unsafe_werkzeug=True)

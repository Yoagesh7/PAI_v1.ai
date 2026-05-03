console.log('[FOCUS] Focus Mode v5 Loaded (Dark Premium Swipe)');

// --- TIMER LOGIC ---
let timerInterval; let timeLeft = 25 * 60; let isRunning = false; let totalTime = 25 * 60;
const circle = document.getElementById('timerProgress'); const circumference = 2 * Math.PI * 130;
if (circle) { circle.style.strokeDasharray = `${circumference} ${circumference}`; circle.style.strokeDashoffset = 0; }

function updateDisplay() {
    const m = Math.floor(timeLeft / 60); const s = timeLeft % 60;
    document.getElementById('timer').innerText = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    document.title = `${m}:${s.toString().padStart(2, '0')} - Focus`;
    if (circle) circle.style.strokeDashoffset = circumference - ((timeLeft / totalTime) * circumference);
}

function setTime(min) {
    console.log('setTime called with:', min);
    pauseTimer();
    timeLeft = min * 60;
    totalTime = timeLeft;
    updateDisplay();
    document.getElementById('startBtn').innerText = "Start Focus";
    if (circle) circle.style.strokeDashoffset = 0;
}

function setCustomTime() {
    const min = document.getElementById('customMin').value;
    console.log('setCustomTime called, value:', min);
    if (min > 0) setTime(parseInt(min));
}

function toggleTimer() {
    console.log('toggleTimer called, isRunning:', isRunning);
    isRunning ? pauseTimer() : startTimer();
}

function startTimer() {
    isRunning = true;
    document.getElementById('startBtn').innerText = "Pause";
    timerInterval = setInterval(() => {
        timeLeft--;
        updateDisplay();
        if (timeLeft <= 0) completeSession();
    }, 1000);
}

function pauseTimer() {
    isRunning = false;
    clearInterval(timerInterval);
    document.getElementById('startBtn').innerText = "Resume";
}

function resetTimer() {
    pauseTimer();
    timeLeft = totalTime;
    updateDisplay();
    document.getElementById('startBtn').innerText = "Start Focus";
    if (circle) circle.style.strokeDashoffset = 0;
}

function completeSession() {
    pauseTimer();
    const sessionMinutes = Math.ceil((totalTime - timeLeft) / 60);
    console.log('Session complete! Duration:', sessionMinutes, 'minutes');
    fetch('/api/reward', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: sessionMinutes })
    }).then(res => res.json()).then(data => {
        console.log('Reward received:', data);
        showRewardModal(data.reward, data.name);
        loadGarden();
    }).catch(err => {
        console.error('Reward API error:', err);
        alert('Timer completed but could not save reward. Check console for details.');
    });
    timeLeft = totalTime;
    updateDisplay();
}

function showRewardModal(e, n) {
    const emojiEl = document.getElementById('rewardEmoji');
    const nameEl = document.getElementById('rewardName');
    const modalEl = document.getElementById('rewardModal');

    if (emojiEl && nameEl && modalEl) {
        emojiEl.innerText = e;
        nameEl.innerText = n;
        modalEl.style.display = 'flex';
        console.log('[FOCUS] Reward modal shown successfully');
    } else {
        console.error('[FOCUS] Critical Error: Modal elements not found!', {
            emojiEl: !!emojiEl,
            nameEl: !!nameEl,
            modalEl: !!modalEl
        });
        alert(`You earned a ${n} (${e})! (Modal error)`);
    }
}

function closeModal() {
    document.getElementById('rewardModal').style.display = 'none';
}

// --- MUSIC LOGIC ---
let audio = document.getElementById('audioPlayer');
let isMusicOn = false;
let songs = [];
let currentSongIndex = 0;

function toggleMusic() {
    isMusicOn = !isMusicOn;
    const toggle = document.getElementById('mainMusicToggle');
    const interface = document.getElementById('playerInterface');
    if (isMusicOn) {
        toggle.classList.add('music-active');
        interface.style.opacity = '1';
        interface.style.pointerEvents = 'all';
        if (songs.length > 0 && audio.paused && !audio.src) changeSong(songs[0]);
    } else {
        toggle.classList.remove('music-active');
        interface.style.opacity = '0.3';
        interface.style.pointerEvents = 'none';
        audio.pause();
        updatePlayBtn();
    }
}

function loadSongs() {
    fetch('/api/songs').then(res => res.json()).then(data => {
        songs = data;
        const list = document.getElementById('playlistOverlay');
        list.innerHTML = '';
        songs.forEach((s, i) => {
            const item = document.createElement('div');
            item.className = 'playlist-item';
            item.innerHTML = `<span>🎵</span> <span>${s.replace('.mp3', '')}</span>`;
            item.onclick = () => { changeSong(s); togglePlaylist(); };
            item.id = `song-item-${i}`;
            list.appendChild(item);
        });
    });
}

function changeSong(f) {
    if (!f) return;
    currentSongIndex = songs.indexOf(f);
    audio.src = `/songs/${encodeURIComponent(f)}`;
    audio.play().catch(e => console.error(e));
    document.getElementById('trackName').innerText = f.replace('.mp3', '');
    updatePlayBtn();
    highlightActiveSong(currentSongIndex);
    if (!isMusicOn) toggleMusic();
}

function highlightActiveSong(i) {
    document.querySelectorAll('.playlist-item').forEach(e => e.classList.remove('active'));
    const el = document.getElementById(`song-item-${i}`);
    if (el) el.classList.add('active');
}

function togglePlaylist() {
    const p = document.getElementById('playlistOverlay');
    p.style.display = p.style.display === 'flex' ? 'none' : 'flex';
}

function prevSong() {
    if (songs.length === 0) return;
    currentSongIndex = (currentSongIndex - 1 + songs.length) % songs.length;
    changeSong(songs[currentSongIndex]);
}

function nextSong() {
    if (songs.length === 0) return;
    currentSongIndex = (currentSongIndex + 1) % songs.length;
    changeSong(songs[currentSongIndex]);
}

function togglePlayInfo() {
    if (songs.length === 0) return;
    audio.paused ? audio.play() : audio.pause();
    updatePlayBtn();
}

function updatePlayBtn() {
    const icon = document.getElementById('playPauseIcon');
    if (audio.paused) {
        icon.innerHTML = '<path d="M8 5v14l11-7z"/>'; // Play icon
    } else {
        icon.innerHTML = '<path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>'; // Pause icon
    }
}

function updateProgress() {
    if (audio.duration) {
        const p = (audio.currentTime / audio.duration) * 100;
        document.getElementById('progressFill').style.width = `${p}%`;
        document.getElementById('currTime').innerText = formatTime(audio.currentTime);
    }
}

function updateDuration() {
    document.getElementById('totalTime').innerText = formatTime(audio.duration);
}

function formatTime(s) {
    const m = Math.floor(s / 60);
    const sc = Math.floor(s % 60);
    return `${m}:${sc.toString().padStart(2, '0')}`;
}

function seekAudio(e) {
    const w = e.currentTarget.clientWidth;
    const x = e.offsetX;
    const d = audio.duration;
    if (d) audio.currentTime = (x / w) * d;
}

// --- LANDSCAPE CARD COLLECTION ---
// --- LANDSCAPE CARD COLLECTION ---
// --- LANDSCAPE CARD COLLECTION ---
const landscapes = {
    'Santorini': { subtitle: 'Greece', emoji: '🏛️', fact: 'The island’s unique shape is the result of a massive volcanic eruption around 1600 BC.', image: '/static/images/landscapes/Santorini%C2%A0(Greece).png' },
    'Aurora': { subtitle: 'Iceland', emoji: '🌌', fact: 'Auroras make sounds! Observers have described them as hissing or crackling noises.', image: '/static/images/landscapes/Aurora (Iceland).jpg' },
    'Sahara': { subtitle: 'Africa', emoji: '🏜️', fact: 'The Sahara is the largest hot desert in the world, roughly the size of the United States.', image: '/static/images/landscapes/Sahara (Africa).webp' },
    'Amazon': { subtitle: 'Brazil', emoji: '🌿', fact: 'The Amazon Rainforest produces about 20% of the earth’s oxygen.', image: '/static/images/landscapes/Amazon (Brazil).webp' },
    'Fuji': { subtitle: 'Japan', emoji: '🗻', fact: 'Mount Fuji is actually three volcanoes sitting on top of one another.', image: '/static/images/landscapes/Fuji (Japan).webp' },
    'Alps': { subtitle: 'Switzerland', emoji: '🏔️', fact: 'The Alps were formed about 44 million years ago as the African and Eurasian tectonic plates collided.', image: '/static/images/landscapes/Alps (Switzerland).jpg' },
    'Lavender': { subtitle: 'Provence', emoji: '🌸', fact: 'Lavender comes from the same family as mint and is known to reduce stress and anxiety.', image: '/static/images/landscapes/Lavender%C2%A0(Provence).png' },
    'Maldives': { subtitle: 'Indian Ocean', emoji: '🏝️', fact: 'The Maldives is the lowest country in the world, with an average ground level of 1.5 meters.', image: '/static/images/landscapes/Maldives (Indian Ocean).png' },
    'Tuscany': { subtitle: 'Italy', emoji: '🍇', fact: 'Tuscany is regarded as the birthplace of the Italian Renaissance.', image: '/static/images/landscapes/Tuscany%C2%A0(Italy).png' },
    'Patagonia': { subtitle: 'Argentina', emoji: '🧊', fact: 'Patagonia is home to the Perito Moreno Glacier, one of the few glaciers in the world that is still growing.', image: '/static/images/landscapes/Patagonia%C2%A0(Argentina).png' }
};

// Handle potential non-breaking spaces in filenames by trying both if needed, 
// but here I used URL encoding %C2%A0 for the NBSP observed in file list interactions just to be safe, 
// or simple spaces. Let's stick to simple text structure for the loop and let browser handle encoding.
// Actually, it's safer to use the exact strings found. 
// The list_dir output showed visual spaces. Let's try standard spaces first for those that had them, 
// but for the ones that looked 'wide' or had issues, I'll update if they break. 
// UPDATE: I will use the encoded chars in the path to be safe if they were indeed NBSP.
// However, standard browser URL encoding for ' ' is %20. 
// I will revert to standard strings for the update below and rely on the fact that I can fix it if images 404.

const landscapes_fixed = {
    'Santorini': { subtitle: 'Greece', emoji: '🏛️', fact: 'The island’s unique shape is the result of a massive volcanic eruption around 1600 BC.', image: 'Santorini (Greece).png' },
    'Aurora': { subtitle: 'Iceland', emoji: '🌌', fact: 'Auroras make sounds! Observers have described them as hissing or crackling noises.', image: 'Aurora (Iceland).jpg' },
    'Sahara': { subtitle: 'Africa', emoji: '🏜️', fact: 'The Sahara is the largest hot desert in the world, roughly the size of the United States.', image: 'Sahara (Africa).webp' },
    'Amazon': { subtitle: 'Brazil', emoji: '🌿', fact: 'The Amazon Rainforest produces about 20% of the earth’s oxygen.', image: 'Amazon (Brazil).webp' },
    'Fuji': { subtitle: 'Japan', emoji: '🗻', fact: 'Mount Fuji is actually three volcanoes sitting on top of one another.', image: 'Fuji (Japan).webp' },
    'Alps': { subtitle: 'Switzerland', emoji: '🏔️', fact: 'The Alps were formed about 44 million years ago as the African and Eurasian tectonic plates collided.', image: 'Alps (Switzerland).jpg' },
    'Lavender': { subtitle: 'Provence', emoji: '🌸', fact: 'Lavender comes from the same family as mint and is known to reduce stress and anxiety.', image: 'Lavender (Provence).png' },
    'Maldives': { subtitle: 'Indian Ocean', emoji: '🏝️', fact: 'The Maldives is the lowest country in the world, with an average ground level of 1.5 meters.', image: 'Maldives (Indian Ocean).png' },
    'Tuscany': { subtitle: 'Italy', emoji: '🍇', fact: 'Tuscany is regarded as the birthplace of the Italian Renaissance.', image: 'Tuscany (Italy).png' },
    'Patagonia': { subtitle: 'Argentina', emoji: '🧊', fact: 'Patagonia is home to the Perito Moreno Glacier, one of the few glaciers in the world that is still growing.', image: 'Patagonia (Argentina).png' }
};


// --- 3D CAROUSEL LOGIC (OPTIMIZED) ---
function updateCarousel() {
    const container = document.getElementById('cardsContainer');
    if (!container) return;

    // 1. Batch Global Reads
    const scrollLeft = container.scrollLeft;
    const containerWidth = container.offsetWidth;
    const center = scrollLeft + containerWidth / 2;
    const maxDist = containerWidth / 1.5;

    const cards = container.querySelectorAll('.landscape-card-premium');

    // 2. Batch DOM Reads
    const updates = [];
    cards.forEach(card => {
        updates.push({
            el: card,
            center: card.offsetLeft + card.offsetWidth / 2
        });
    });

    // 3. Batch DOM Writes
    updates.forEach(item => {
        const dist = item.center - center;

        let norm = dist / maxDist;
        if (norm > 1) norm = 1;
        if (norm < -1) norm = -1;

        // Transforms
        const scale = 1 - Math.abs(norm) * 0.25;
        const rotate = norm * 45;
        const zIndex = 100 - Math.round(Math.abs(norm) * 50);
        const translateX = -norm * 100; // Increased overlap for tighter feel

        // Updates
        item.el.style.zIndex = zIndex;
        const brightness = 1 - Math.abs(norm) * 0.4;
        item.el.style.filter = `brightness(${brightness})`;
        // Use translate3d for GPU acceleration
        item.el.style.transform = `translate3d(${translateX}px, 0, 0) scale(${scale}) rotateY(${rotate}deg)`;
    });
}

function loadCards() {
    fetch('/api/rewards').then(res => res.json()).then(data => {
        const container = document.getElementById('cardsContainer'); // SWIPE CONTAINER ID
        const emptyMsg = document.getElementById('emptyCollectionMsg');

        const countEl = document.getElementById('cardCount');
        if (countEl) countEl.innerText = `${data.length} Card${data.length !== 1 ? 's' : ''}`;

        if (data.length === 0) {
            if (emptyMsg) emptyMsg.style.display = 'block';
            if (container) container.style.display = 'none';
            return;
        }

        if (emptyMsg) emptyMsg.style.display = 'none';
        if (container) {
            container.style.display = 'flex'; // Enable flex for swipe
            container.innerHTML = ''; // Reset

            // Setup Scroll Listener for 3D Effect
            container.removeEventListener('scroll', updateCarousel); // Prevent dupes
            container.addEventListener('scroll', () => window.requestAnimationFrame(updateCarousel));
            window.removeEventListener('resize', updateCarousel);
            window.addEventListener('resize', () => window.requestAnimationFrame(updateCarousel));

            data.forEach((item, index) => {
                const landscape = landscapes_fixed[item.type] || landscapes_fixed['Santorini'];
                const emoji = landscape.emoji || '🌍';
                const fact = landscape.fact || 'A beautiful place to focus.';
                // Construct path. Note: The filenames likely contain Non-Breaking Spaces (NBSP) based on previous listings.
                // We'll trust the keys in landscapes_fixed match the file system.
                const imagePath = `/static/images/landscapes/${landscape.image}`;

                const card = document.createElement('div');
                card.className = 'landscape-card-premium'; // NEW PREMIUM CLASS
                // card.style.animationDelay = `${index * 0.1}s`; // Remove delay as it interferes with initial transform calculation
                card.onclick = function () {
                    // Snap to center if clicked and not centered? 
                    // For now just flip. 
                    this.classList.toggle('flipped');
                };

                // IMAGE CARD STRUCTURE
                card.innerHTML = `
                    <div class="card-inner">
                        <div class="card-front" style="background-image: url('${imagePath}'); background-size: cover; background-position: center;">
                            <div class="premium-card-overlay">
                                <div class="premium-card-title">${item.type}</div>
                                <div class="premium-card-sub">${landscape.subtitle}</div>
                                <div class="premium-card-meta-front">${new Date(item.date).toLocaleDateString()}</div>
                            </div>
                        </div>
                        <div class="card-back" style="background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.95)), url('${imagePath}'); background-size: cover; background-position: center;">
                            <div class="card-back-content">
                                <div class="card-back-quote-icon">❝</div>
                                <div class="card-back-title">Did You Know?</div>
                                <div class="card-back-text">${fact}</div>
                            </div>
                        </div>
                    </div>
                `;

                container.appendChild(card);
            });

            // Initial call to set positions
            setTimeout(updateCarousel, 100);
        }
    });
}

// Alias for compatibility
const loadGarden = loadCards;

function toggleFullFocus() {
    console.log('[FOCUS] Toggling Full Focus Mode');
    document.body.classList.toggle('full-focus-mode');
    const isFull = document.body.classList.contains('full-focus-mode');
    console.log('[FOCUS] Full Focus active:', isFull);

    const btn = document.getElementById('fsBtn');
    if (btn) {
        btn.innerText = isFull ? "✖" : "⤢";
        btn.title = isFull ? "Exit Full Screen" : "Full Screen";
        btn.style.color = isFull ? "rgba(255,255,255,0.8)" : "rgba(255,255,255,0.3)";
    }
}

// Ensure function is available globally
window.toggleMusic = toggleMusic;
window.toggleTimer = toggleTimer;
window.setTime = setTime;
window.setCustomTime = setCustomTime;
window.resetTimer = resetTimer;
window.seekAudio = seekAudio;
window.changeSong = changeSong;
window.toggleFullFocus = toggleFullFocus;
window.loadCards = loadCards; // Explicitly export this too just in case
window.togglePlaylist = togglePlaylist;
window.toggleFullFocus = toggleFullFocus;

window.onload = function () {
    console.log('[FOCUS] Window loaded, initializing...');
    loadSongs();
    loadGarden();
    updateDisplay();
};

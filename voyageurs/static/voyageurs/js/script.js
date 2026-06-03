function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ================= MATCHING STORAGE =================
function selectionnerVoyageur(voyageurId) {
    localStorage.setItem('match_data', JSON.stringify({
        type: 'expediteur',
        voyageur_id: parseInt(voyageurId)
    }));
    afficherModalConnexion('expediteur');
}

function selectionnerExpediteur(expediteurId) {
    localStorage.setItem('match_data', JSON.stringify({
        type: 'voyageur',
        expediteur_id: parseInt(expediteurId)
    }));
    localStorage.setItem('expediteur_a_preremplir', expediteurId);
    afficherModalConnexion('voyageur');
}

// ================= MODAL CONNEXION =================
function afficherModalConnexion(type) {
    const existant = document.getElementById('modal-connexion-google');
    if (existant) existant.remove();

    const label = type === 'expediteur' ? 'expéditeur' : 'voyageur';

    const modal = document.createElement('div');
    modal.id = 'modal-connexion-google';
    modal.style.cssText = `
        position:fixed;inset:0;background:rgba(0,0,0,0.55);
        display:flex;align-items:center;justify-content:center;
        z-index:9999;backdrop-filter:blur(4px);
    `;

    modal.innerHTML = `
        <div style="background:white;border-radius:20px;padding:36px 32px;max-width:440px;
                    width:92%;box-shadow:0 24px 64px rgba(0,0,0,0.3);
                    text-align:center;position:relative;">
            <button onclick="fermerModalGoogle()"
                    style="position:absolute;top:14px;right:18px;background:none;
                           border:none;font-size:1.6rem;cursor:pointer;color:#bbb;">×</button>
            <div style="font-size:2.8rem;margin-bottom:12px;">🔐</div>
            <h3 style="color:#0A1F44;margin-bottom:8px;font-size:1.15rem;font-weight:700;">
                Rejoignez KERALINK en tant que ${label}
            </h3>
            <p style="color:#888;font-size:0.88rem;margin-bottom:26px;line-height:1.5;">
                Connectez-vous ou créez votre compte pour continuer.
            </p>
            <a href="/accounts/google/login/?next=/google-callback/"
               style="display:flex;align-items:center;justify-content:center;gap:12px;
                      width:100%;padding:15px;border-radius:12px;background:white;
                      border:2.5px solid #e0e0e0;color:#333;font-weight:700;font-size:1rem;
                      text-decoration:none;margin-bottom:14px;transition:all 0.25s;
                      box-shadow:0 2px 8px rgba(0,0,0,0.07);"
               onmouseover="this.style.borderColor='#4285F4';this.style.transform='translateY(-2px)'"
               onmouseout="this.style.borderColor='#e0e0e0';this.style.transform='none'">
                <svg width="22" height="22" viewBox="0 0 48 48">
                    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                </svg>
                Continuer avec Google
            </a>
            <div style="display:flex;align-items:center;gap:12px;margin:14px 0;">
                <div style="flex:1;height:1px;background:#eee;"></div>
                <span style="color:#bbb;font-size:0.82rem;">ou</span>
                <div style="flex:1;height:1px;background:#eee;"></div>
            </div>
            <button onclick="fermerModalGoogle(); showPage(null, 'profil'); setTimeout(activerModeMatching, 300);"
                    style="width:100%;padding:13px;border-radius:12px;
                           background:linear-gradient(90deg,#0A1F44,#1E3A8A);color:white;
                           border:none;font-weight:700;font-size:0.95rem;cursor:pointer;
                           margin-bottom:10px;transition:all 0.2s;"
                    onmouseover="this.style.opacity='0.9'"
                    onmouseout="this.style.opacity='1'">
                ✍️ S'inscrire manuellement
            </button>
            <button onclick="fermerModalGoogle(); showPage(null, 'login');"
                    style="width:100%;padding:11px;border-radius:12px;background:transparent;
                           border:1.5px solid #ddd;color:#555;font-size:0.9rem;font-weight:600;
                           cursor:pointer;transition:all 0.2s;"
                    onmouseover="this.style.borderColor='#FF7A00';this.style.color='#FF7A00'"
                    onmouseout="this.style.borderColor='#ddd';this.style.color='#555'">
                🔑 J'ai déjà un compte
            </button>
        </div>
    `;

    modal.addEventListener('click', (e) => { if (e.target === modal) fermerModalGoogle(); });
    document.body.appendChild(modal);
}

function fermerModalGoogle() {
    const modal = document.getElementById('modal-connexion-google');
    if (modal) modal.remove();
}

// ================= ACTIVER MODE MATCHING =================
function activerModeMatching() {
    const match = JSON.parse(localStorage.getItem('match_data') || '{}');

    if (match.type === 'expediteur') {
        const btn = document.getElementById('exp-submit');
        if (btn) btn.textContent = "Accepter le trajet";
        const modalTitle = document.querySelector('#expediteur-modal .modal-title');
        if (modalTitle) modalTitle.textContent = "Confirmer le matching avec le voyageur";
        // ✅ Préremplir le formulaire expéditeur depuis l'annonce du voyageur
        setTimeout(preremplirFormulaireExpediteur, 400);
    }
    else if (match.type === 'voyageur') {
        const btn = document.getElementById('voy-submit');
        if (btn) btn.textContent = "Accepter sa demande";
        setTimeout(preremplirFormulaireVoyageur, 400);
    }
}

// ✅ NOUVEAU : préremplir formulaire expéditeur depuis annonce voyageur
function preremplirFormulaireExpediteur() {
    const match = JSON.parse(localStorage.getItem('match_data') || '{}');
    if (!match.voyageur_id) return;

    fetch(`/get-voyageur-info/?voyageur_id=${match.voyageur_id}`)
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            const champs = {
                'exp-pays': data.pays_depart,
                'exp-ville': data.ville_depart,
                'exp-pays-dest': data.pays_destination,
                'exp-ville-dest': data.ville_destination,
            };
            Object.entries(champs).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el && val) {
                    el.value = val;
                    el.style.background = '#fffde7';
                    el.style.borderColor = '#FF7A00';
                    el.setAttribute('readonly', 'readonly');
                }
            });
            // Limiter le poids au maximum disponible
            const poidsEl = document.getElementById('exp-poids');
            if (poidsEl) {
                poidsEl.max = data.poids_disponible;
                poidsEl.placeholder = `Max ${data.poids_disponible} kg disponibles`;
            }
            verifierFormulaireExpediteur();
            showAlert(`✅ Trajet pré-rempli ! Max ${data.poids_disponible} kg disponibles.`, "success");
        }
    })
    .catch(() => {});
}

// ================= PRÉREMPLISSAGE FORMULAIRE VOYAGEUR =================
function preremplirFormulaireVoyageur() {
    const expId = localStorage.getItem('expediteur_a_preremplir');
    if (!expId) return;

    fetch(`/get-expediteur-info/?expediteur_id=${expId}`)
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            const champs = {
                'voy-pays-depart': data.pays_depart,
                'voy-ville-depart': data.ville_depart,
                'voy-pays-destination': data.pays_destination,
                'voy-ville-destination': data.ville_destination,
                'voy-poids': data.poids
            };
            let rempli = false;
            Object.entries(champs).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el && val) {
                    el.value = val;
                    el.style.background = '#fffde7';
                    el.style.borderColor = '#FF7A00';
                    rempli = true;
                }
            });
            if (rempli) {
                verifierFormulaireVoyageur();
                showAlert("✅ Formulaire pré-rempli depuis l'annonce de l'expéditeur", "success");
            }
        }
    })
    .catch(() => {});
}

// ✅ NOUVEAU : Préremplir nom/téléphone depuis le profil connecté
function preremplirDepuisProfil() {
    const profilData = JSON.parse(localStorage.getItem('profil_connecte') || '{}');
    if (!profilData.nom_complet) return;

    // Formulaire voyageur
    const nomParts = profilData.nom_complet.trim().split(' ');
    const prenom = nomParts[0] || '';
    const nom = nomParts.slice(1).join(' ') || '';

    const voyNom = document.getElementById('voy-nom');
    const voyPrenom = document.getElementById('voy-prenom');
    const voyTel = document.getElementById('voy-telephone');

    if (voyNom && nom) voyNom.value = nom;
    if (voyPrenom && prenom) voyPrenom.value = prenom;
    if (voyTel && profilData.telephone) voyTel.value = profilData.telephone;

    // Formulaire expéditeur
    const expNom = document.getElementById('exp-nom');
    const expPrenom = document.getElementById('exp-prenom');
    const expTel = document.getElementById('exp-telephone');

    if (expNom && nom) expNom.value = nom;
    if (expPrenom && prenom) expPrenom.value = prenom;
    if (expTel && profilData.telephone) expTel.value = profilData.telephone;
}

// ================= CONFIRMER ENVOI EXPÉDITEUR =================
function confirmerEnvoi() {
    const formData = new FormData();
    const poids = parseFloat(document.getElementById('exp-poids').value) || 0;
    const prix_reel = poids * 10.20;

    const nom = document.getElementById('exp-nom').value;
    const prenom = document.getElementById('exp-prenom').value;
    const modePaiement = document.getElementById('selected-payment').value;
    const montant = (poids * 10.20).toFixed(2);

    formData.append('nom', nom);
    formData.append('prenom', prenom);
    formData.append('telephone', document.getElementById('exp-telephone').value);
    formData.append('pays', document.getElementById('exp-pays').value);
    formData.append('ville', document.getElementById('exp-ville').value);
    formData.append('pays_destination', document.getElementById('exp-pays-dest').value);
    formData.append('ville_destination', document.getElementById('exp-ville-dest').value);
    formData.append('poids', poids);
    formData.append('prix', prix_reel);
    formData.append('mode_paiement', modePaiement);

    const match = JSON.parse(localStorage.getItem('match_data') || '{}');

    if (match.type === 'expediteur' && match.voyageur_id) {
        formData.append('mode', 'matching');
        formData.append('voyageur_id', match.voyageur_id);
    } else {
        formData.append('mode', 'normal');
    }

    fetch('/ajouter-expediteur/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            closeModal('expediteur');

            localStorage.setItem('annonce_data', JSON.stringify({
                type: 'expediteur',
                id: data.expediteur_id
            }));

            if (match.type === 'expediteur') {
                localStorage.removeItem('match_data');
            }

            document.getElementById('expediteur-form').reset();
            document.querySelectorAll('.payment-option').forEach(opt => opt.classList.remove('selected'));
            document.getElementById('selected-payment').value = '';
            document.getElementById('exp-total').textContent = '0.00 €';

            showAlert("💳 Redirection vers le paiement...", "success");
            setTimeout(() => {
                window.location.href = `/paiement/?expediteur_id=${data.expediteur_id}&mode_paiement=${modePaiement}&montant=${montant}`;
            }, 1000);
        } else {
            showAlert("Erreur : " + (data.message || "Inconnue"));
        }
    })
    .catch(() => showAlert("Erreur de connexion"));
}

// ================= CONFIRMER PUBLICATION VOYAGEUR =================
function confirmerPublication() {
    const formData = new FormData();
    const nom = document.getElementById('voy-nom').value;
    const prenom = document.getElementById('voy-prenom').value;

    formData.append('nom', nom);
    formData.append('prenom', prenom);
    formData.append('telephone', document.getElementById('voy-telephone').value);
    formData.append('pays_depart', document.getElementById('voy-pays-depart').value);
    formData.append('ville_depart', document.getElementById('voy-ville-depart').value);
    formData.append('pays_destination', document.getElementById('voy-pays-destination').value);
    formData.append('ville_destination', document.getElementById('voy-ville-destination').value);
    formData.append('date_depart', document.getElementById('voy-date-depart').value);
    formData.append('heure_depart', document.getElementById('voy-heure-depart').value);
    formData.append('date_arrivee', document.getElementById('voy-date-arrivee').value);
    formData.append('heure_arrivee', document.getElementById('voy-heure-arrivee').value);
    formData.append('poids', document.getElementById('voy-poids').value);
    formData.append('type_kg', document.querySelector('input[name="type_kg"]:checked').value);

    const match = JSON.parse(localStorage.getItem('match_data') || '{}');

    if (match.type === 'voyageur' && match.expediteur_id) {
        formData.append('mode', 'matching');
        formData.append('expediteur_id', match.expediteur_id);
    } else {
        formData.append('mode', 'normal');
    }

    fetch('/ajouter-voyageur/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            closeModal('voyageur');

            localStorage.setItem('annonce_data', JSON.stringify({
                type: 'voyageur',
                id: data.voyageur_id
            }));
            localStorage.removeItem('expediteur_a_preremplir');

            if (match.type === 'voyageur') {
                // ✅ MODE MATCHING → espace connecté directement
                localStorage.removeItem('match_data');
                showAlert("✅ Matching créé avec succès !", "success");
                document.getElementById('voyageur-form').reset();
                document.getElementById('voy-gain').textContent = '0.00 €';
                setTimeout(() => { window.location.href = '/espace-connecte/'; }, 1200);
            } else {
                // MODE NORMAL → page profil
                showAlert("🧳 Trajet publié ! Créez votre profil.", "success");
                document.getElementById('voyageur-form').reset();
                document.getElementById('voy-gain').textContent = '0.00 €';
                setTimeout(() => { preremplirProfil(prenom + ' ' + nom, 'voyageur'); }, 1500);
            }
        } else {
            showAlert("Erreur : " + (data.message || "Inconnue"));
        }
    });
}

// ================= PRÉ-REMPLISSAGE PROFIL =================
function preremplirProfil(nomComplet, type) {
    showPage(null, 'profil');
    setTimeout(() => {
        const champNom = document.getElementById('nom_complet');
        if (champNom) champNom.value = nomComplet;
        choisirType(type);
        showAlert("👤 Complétez votre profil pour accéder à votre espace !", "success");
    }, 200);
}

// ================= INSCRIPTION PROFIL =================
function inscrireProfil() {
    const champs = ['nom_complet', 'username', 'email', 'telephone', 'password', 'profil-password2'];
    for (let id of champs) {
        const champ = document.getElementById(id);
        if (!champ || !champ.value.trim()) {
            showAlert(`⚠️ Le champ est obligatoire`);
            if (champ) champ.focus();
            return;
        }
    }

    const type = document.getElementById('type_profil').value;
    if (!type) { showAlert("⚠️ Choisis Voyageur ou Expéditeur"); return; }

    const password = document.getElementById('password').value;
    const password2 = document.getElementById('profil-password2').value;
    if (password !== password2) { showAlert("❌ Les mots de passe ne correspondent pas"); return; }
    if (password.length < 4) { showAlert("❌ Mot de passe trop court (4 min)"); return; }

    const nomComplet = document.getElementById('nom_complet').value;
    const telephone = document.getElementById('telephone').value;

    const formData = new FormData();
    formData.append('type_profil', type);
    formData.append('nom_complet', nomComplet);
    formData.append('username', document.getElementById('username').value);
    formData.append('email', document.getElementById('email').value);
    formData.append('telephone', telephone);
    formData.append('password', password);

    const annonce = JSON.parse(localStorage.getItem('annonce_data') || '{}');
    if (annonce.type === 'expediteur' && annonce.id) formData.append('expediteur_id', annonce.id);
    else if (annonce.type === 'voyageur' && annonce.id) formData.append('voyageur_id', annonce.id);

    fetch('/creer-profil/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            showAlert("✅ Profil créé !");
            localStorage.removeItem('annonce_data');

            // ✅ Sauvegarder les infos profil pour préremplissage des formulaires
            localStorage.setItem('profil_connecte', JSON.stringify({
                nom_complet: nomComplet,
                telephone: telephone,
                type_profil: type
            }));

            const match = JSON.parse(localStorage.getItem('match_data') || '{}');

            // ✅ CAS MATCHING : rediriger vers le bon formulaire AVEC préremplissage
            if (match && match.type) {
                if (match.type === 'voyageur') {
                    // Voyageur vient de s'inscrire → aller page Voyager avec préremplissage
                    setTimeout(() => {
                        showPage(null, 'voyageur');
                        setTimeout(() => {
                            activerModeMatching();
                            preremplirDepuisProfil();
                        }, 300);
                    }, 800);
                } else if (match.type === 'expediteur') {
                    // Expéditeur vient de s'inscrire → aller page Expédier avec préremplissage
                    setTimeout(() => {
                        showPage(null, 'expediteur');
                        setTimeout(() => {
                            activerModeMatching();
                            preremplirDepuisProfil();
                        }, 300);
                    }, 800);
                }
                return;
            }

            // CAS NORMAL → espace connecté
            setTimeout(() => { window.location.href = '/espace-connecte/'; }, 1200);
        } else {
            showAlert("❌ " + (data.message || "Erreur"));
        }
    });
}

// ================= CONNEXION =================
function performLogin() {
    const identifiant = document.getElementById('login-identifiant').value.trim();
    const password = document.getElementById('login-password').value;
    if (!identifiant || !password) { showAlert("⚠️ Veuillez remplir tous les champs"); return; }

    const formData = new FormData();
    formData.append('username', identifiant);
    formData.append('password', password);

    fetch('/login-profil/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            showAlert("✅ Connexion réussie", "success");

            // ✅ Sauvegarder infos profil pour préremplissage
            localStorage.setItem('profil_connecte', JSON.stringify({
                nom_complet: data.nom_complet || '',
                telephone: data.telephone || '',
                type_profil: data.type_profil
            }));

            const match = JSON.parse(localStorage.getItem('match_data') || '{}');

            if (match && match.type) {
                // ✅ Cas matching après login
                _gererMatchingApresLogin(match, data);
            } else {
                setTimeout(() => { window.location.href = '/espace-connecte/'; }, 800);
            }
        } else {
            showAlert("❌ " + (data.message || "Identifiants incorrects"));
        }
    });
}

function _gererMatchingApresLogin(match, profilData) {
    if (match.type === 'voyageur') {
        // Un voyageur connecté a cliqué sur un expéditeur
        // → aller page Voyager avec préremplissage (comme si c'était une inscription)
        localStorage.removeItem('expediteur_a_preremplir');
        localStorage.setItem('expediteur_a_preremplir', match.expediteur_id);

        setTimeout(() => {
            showPage(null, 'voyageur');
            setTimeout(() => {
                activerModeMatching();
                preremplirDepuisProfil();
                preremplirFormulaireVoyageur();
            }, 300);
        }, 600);

    } else if (match.type === 'expediteur') {
        // Un expéditeur connecté a cliqué sur un voyageur
        // ✅ NOUVEAU : proposer directement le paiement
        _proposerPaiementDirectExpéditeur(match.voyageur_id, profilData);
    }
}

// ✅ NOUVEAU : Expéditeur connecté → modal de paiement direct
function _proposerPaiementDirectExpéditeur(voyageurId, profilData) {
    // Récupérer les infos du voyageur pour calculer le montant
    fetch(`/get-voyageur-info/?voyageur_id=${voyageurId}`)
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            const poids = data.poids_disponible;
            const prix = poids * 10;
            const commission = poids * 0.20;
            const total = (poids * 10.20).toFixed(2);

            // Afficher modal de paiement direct
            afficherModalPaiementDirect(voyageurId, data, total, prix, commission, profilData);
        } else {
            // Fallback : aller à la page expéditeur
            showPage(null, 'expediteur');
            setTimeout(() => { activerModeMatching(); preremplirDepuisProfil(); }, 300);
        }
    })
    .catch(() => {
        showPage(null, 'expediteur');
        setTimeout(() => { activerModeMatching(); preremplirDepuisProfil(); }, 300);
    });
}

function afficherModalPaiementDirect(voyageurId, voyageurData, total, prix, commission, profilData) {
    const existant = document.getElementById('modal-paiement-direct');
    if (existant) existant.remove();

    const modal = document.createElement('div');
    modal.id = 'modal-paiement-direct';
    modal.style.cssText = `
        position:fixed;inset:0;background:rgba(0,0,0,0.6);
        display:flex;align-items:center;justify-content:center;
        z-index:9999;backdrop-filter:blur(5px);
    `;

    modal.innerHTML = `
        <div style="background:white;border-radius:20px;padding:0;max-width:480px;
                    width:92%;box-shadow:0 24px 64px rgba(0,0,0,0.35);overflow:hidden;">

            <!-- Header -->
            <div style="background:linear-gradient(120deg,#0A1F44,#1E3A8A);
                        padding:20px 24px;color:white;text-align:center;">
                <div style="font-size:1.1rem;font-weight:700;margin-bottom:4px;">💳 Paiement du trajet</div>
                <div style="font-size:0.85rem;opacity:0.8;">
                    ${voyageurData.ville_depart} → ${voyageurData.ville_destination}
                </div>
                <div style="font-size:2rem;font-weight:900;color:#FF7A00;margin-top:8px;">${total} €</div>
                <div style="font-size:0.78rem;opacity:0.7;margin-top:2px;">
                    ${voyageurData.poids_disponible} kg × 10€/kg + commission
                </div>
            </div>

            <div style="padding:24px;">
                <!-- Détail prix -->
                <div style="background:#f9f9f9;border-radius:10px;padding:14px;margin-bottom:16px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:6px;font-size:0.88rem;">
                        <span style="color:#666;">Prix transport</span>
                        <strong>${prix.toFixed(2)} €</strong>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:6px;font-size:0.88rem;">
                        <span style="color:#666;">Commission KERALINK</span>
                        <strong style="color:#e65100;">${commission.toFixed(2)} €</strong>
                    </div>
                    <div style="border-top:1px solid #eee;margin-top:8px;padding-top:8px;
                                display:flex;justify-content:space-between;">
                        <strong>Total TTC</strong>
                        <strong style="color:#FF7A00;font-size:1.1rem;">${total} €</strong>
                    </div>
                </div>

                <!-- Infos expéditeur à compléter -->
                <div style="margin-bottom:16px;">
                    <label style="font-size:0.82rem;color:#555;display:block;margin-bottom:8px;font-weight:600;">
                        📦 Informations du colis
                    </label>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
                        <input id="dp-pays" type="text" placeholder="Pays départ *"
                               style="padding:10px;border-radius:8px;border:1.5px solid #e0e0e0;font-size:0.88rem;outline:none;">
                        <input id="dp-ville" type="text" placeholder="Ville départ *"
                               value="${voyageurData.ville_depart}"
                               style="padding:10px;border-radius:8px;border:1.5px solid #e0e0e0;font-size:0.88rem;outline:none;">
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
                        <input id="dp-pays-dest" type="text" placeholder="Pays destination *"
                               style="padding:10px;border-radius:8px;border:1.5px solid #e0e0e0;font-size:0.88rem;outline:none;">
                        <input id="dp-ville-dest" type="text" placeholder="Ville destination *"
                               value="${voyageurData.ville_destination}"
                               style="padding:10px;border-radius:8px;border:1.5px solid #e0e0e0;font-size:0.88rem;outline:none;">
                    </div>
                    <input id="dp-poids" type="number" placeholder="Poids de votre colis (kg) *"
                           max="${voyageurData.poids_disponible}" step="0.1"
                           style="width:100%;padding:10px;border-radius:8px;border:1.5px solid #e0e0e0;font-size:0.88rem;outline:none;margin-bottom:8px;">
                    <div style="font-size:0.78rem;color:#888;">Max : ${voyageurData.poids_disponible} kg disponibles</div>
                </div>

                <!-- Choix paiement -->
                <div style="margin-bottom:16px;">
                    <label style="font-size:0.82rem;color:#555;display:block;margin-bottom:8px;font-weight:600;">
                        💳 Mode de paiement
                    </label>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                        <div onclick="selectDP(this,'carte')"
                             style="padding:10px;text-align:center;border-radius:8px;
                                    border:2px solid #e0e0e0;cursor:pointer;font-size:0.85rem;transition:0.2s;">
                            💳 Carte
                        </div>
                        <div onclick="selectDP(this,'paypal')"
                             style="padding:10px;text-align:center;border-radius:8px;
                                    border:2px solid #e0e0e0;cursor:pointer;font-size:0.85rem;transition:0.2s;">
                            🅿️ PayPal
                        </div>
                        <div onclick="selectDP(this,'orange')"
                             style="padding:10px;text-align:center;border-radius:8px;
                                    border:2px solid #e0e0e0;cursor:pointer;font-size:0.85rem;transition:0.2s;">
                            🟠 Orange
                        </div>
                        <div onclick="selectDP(this,'wave')"
                             style="padding:10px;text-align:center;border-radius:8px;
                                    border:2px solid #e0e0e0;cursor:pointer;font-size:0.85rem;transition:0.2s;">
                            🌊 Wave
                        </div>
                    </div>
                    <input type="hidden" id="dp-payment-method">
                </div>

                <div style="display:flex;gap:10px;">
                    <button onclick="fermerModalPaiementDirect()"
                            style="flex:1;padding:12px;border-radius:10px;background:#f5f5f5;
                                   border:none;color:#555;font-weight:600;cursor:pointer;font-size:0.9rem;">
                        Annuler
                    </button>
                    <button onclick="validerPaiementDirect('${voyageurId}', ${voyageurData.poids_disponible})"
                            style="flex:2;padding:12px;border-radius:10px;
                                   background:linear-gradient(90deg,#FF7A00,#e66900);
                                   color:white;border:none;font-weight:700;cursor:pointer;font-size:0.95rem;">
                        💸 Procéder au paiement
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

function selectDP(el, mode) {
    document.querySelectorAll('#modal-paiement-direct [onclick^="selectDP"]').forEach(d => {
        d.style.borderColor = '#e0e0e0';
        d.style.background = 'white';
        d.style.color = '#333';
    });
    el.style.borderColor = '#FF7A00';
    el.style.background = '#fff3e0';
    el.style.color = '#e65100';
    document.getElementById('dp-payment-method').value = mode;
}

function fermerModalPaiementDirect() {
    const m = document.getElementById('modal-paiement-direct');
    if (m) m.remove();
    localStorage.removeItem('match_data');
}

function validerPaiementDirect(voyageurId, maxPoids) {
    const pays = document.getElementById('dp-pays').value.trim();
    const ville = document.getElementById('dp-ville').value.trim();
    const paysDest = document.getElementById('dp-pays-dest').value.trim();
    const villeDest = document.getElementById('dp-ville-dest').value.trim();
    const poids = parseFloat(document.getElementById('dp-poids').value);
    const modePaiement = document.getElementById('dp-payment-method').value;

    if (!pays || !ville || !paysDest || !villeDest) {
        showAlert("⚠️ Remplissez toutes les informations du colis"); return;
    }
    if (!poids || poids <= 0 || poids > maxPoids) {
        showAlert(`⚠️ Poids invalide (max ${maxPoids} kg)`); return;
    }
    if (!modePaiement) {
        showAlert("⚠️ Choisissez un mode de paiement"); return;
    }

    const montant = (poids * 10.20).toFixed(2);

    // ✅ Créer l'expéditeur en mode matching puis rediriger vers paiement
    const profilData = JSON.parse(localStorage.getItem('profil_connecte') || '{}');
    const nomParts = (profilData.nom_complet || 'Utilisateur').split(' ');
    const prenom = nomParts[0] || 'Utilisateur';
    const nom = nomParts.slice(1).join(' ') || prenom;

    const formData = new FormData();
    formData.append('nom', nom);
    formData.append('prenom', prenom);
    formData.append('telephone', profilData.telephone || '');
    formData.append('pays', pays);
    formData.append('ville', ville);
    formData.append('pays_destination', paysDest);
    formData.append('ville_destination', villeDest);
    formData.append('poids', poids);
    formData.append('prix', poids * 10.20);
    formData.append('mode_paiement', modePaiement);
    formData.append('mode', 'matching');
    formData.append('voyageur_id', voyageurId);

    fetch('/ajouter-expediteur/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            localStorage.removeItem('match_data');
            fermerModalPaiementDirect();
            showAlert("💳 Redirection vers le paiement...", "success");
            setTimeout(() => {
                window.location.href = `/paiement/?expediteur_id=${data.expediteur_id}&mode_paiement=${modePaiement}&montant=${montant}`;
            }, 800);
        } else {
            showAlert("❌ " + (data.message || "Erreur"));
        }
    });
}

// ================= SHOW ALERT =================
function showAlert(message, type = "default") {
    const alert = document.createElement("div");
    alert.style.cssText = `
        position:fixed;top:20px;right:20px;z-index:99999;
        background:${type === "success" ? "#28a745" : "#ff7a00"};
        color:white;padding:14px 20px;border-radius:10px;
        font-size:0.92rem;font-weight:500;
        box-shadow:0 4px 16px rgba(0,0,0,0.2);
        max-width:360px;line-height:1.4;
    `;
    alert.innerText = message;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 4000);
}

// ================= NAVIGATION =================
function showPage(event, pageId) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    const target = document.getElementById(pageId + '-page');
    if (target) target.classList.add('active');
    document.querySelectorAll('.nav-links a').forEach(link => link.classList.remove('active'));
    if (event) event.target.classList.add('active');
    setTimeout(activerModeMatching, 150);
}

function showLoginForm() { showPage(null, 'login'); }

// ================= INITIALISATION =================
document.addEventListener('DOMContentLoaded', function () {
    showPage(null, 'home');
    activerModeMatching();

    const formExp = document.getElementById('expediteur-form');
    if (formExp) formExp.addEventListener('submit', e => { e.preventDefault(); ouvrirModalExpediteur(); });

    const formVoy = document.getElementById('voyageur-form');
    if (formVoy) formVoy.addEventListener('submit', e => { e.preventDefault(); ouvrirModalVoyageur(); });

    document.querySelectorAll('#voyageur-form input').forEach(i => i.addEventListener('input', verifierFormulaireVoyageur));
    document.querySelectorAll('#expediteur-form input').forEach(i => i.addEventListener('input', verifierFormulaireExpediteur));

    verifierFormulaireVoyageur();
    verifierFormulaireExpediteur();
});

// ================= UTILITAIRES =================
// ✅ CORRECTIF MENU TOUTES — remplace la fonction existante
function toggleMenu() {
    const menu = document.getElementById('menu-dropdown');
    if (!menu) return;
    const isOpen = menu.style.display === 'block';
    menu.style.display = isOpen ? 'none' : 'block';
}

// Fermer le menu "Toutes" quand on clique ailleurs
document.addEventListener('click', function(e) {
    const menuAll = document.querySelector('.menu-all');
    const dropdown = document.getElementById('menu-dropdown');
    if (dropdown && menuAll && !menuAll.contains(e.target)) {
        dropdown.style.display = 'none';
    }
});

function scrollToSection(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    document.getElementById('menu-dropdown').style.display = 'none';
}

function searchHome() {
    const input = document.getElementById('search-input').value.toLowerCase();
    document.querySelectorAll('.traveler-card').forEach(card => {
        card.style.display = card.innerText.toLowerCase().includes(input) ? 'flex' : 'none';
    });
}

function calculerPrixExpediteur() {
    const poids = parseFloat(document.getElementById('exp-poids').value);
    if (!isNaN(poids) && poids > 0)
        document.getElementById('exp-total').textContent = (poids * 10).toFixed(2) + ' €';
    verifierFormulaireExpediteur();
}

function calculerGainVoyageur() {
    const poids = parseFloat(document.getElementById('voy-poids').value);
    document.getElementById('voy-gain').textContent =
        (!isNaN(poids) && poids > 0) ? (poids * 10).toFixed(2) + ' €' : '0.00 €';
}

function selectPayment(element, method) {
    document.querySelectorAll('.payment-option').forEach(opt => opt.classList.remove('selected'));
    element.classList.add('selected');
    document.getElementById('selected-payment').value = method;
    verifierFormulaireExpediteur();
}

function verifierFormulaireExpediteur() {
    const required = ['exp-nom','exp-prenom','exp-telephone','exp-pays','exp-ville',
                      'exp-pays-dest','exp-ville-dest','exp-poids'];
    const valid = required.every(id => document.getElementById(id)?.value?.trim());
    const check1 = document.getElementById('exp-check1')?.checked;
    const check2 = document.getElementById('exp-check2')?.checked;
    const payment = document.getElementById('selected-payment')?.value;
    const btn = document.getElementById('exp-submit');
    if (btn) btn.disabled = !(valid && check1 && check2 && payment);
}

function verifierFormulaireVoyageur() {
    const required = ['voy-nom','voy-prenom','voy-telephone','voy-pays-depart','voy-ville-depart',
                      'voy-pays-destination','voy-ville-destination','voy-date-depart',
                      'voy-heure-depart','voy-date-arrivee','voy-heure-arrivee','voy-poids'];
    const valid = required.every(id => document.getElementById(id)?.value?.trim());
    const check1 = document.getElementById('voy-check1')?.checked;
    const check2 = document.getElementById('voy-check2')?.checked;
    const btn = document.getElementById('voy-submit');
    if (btn) btn.disabled = !(valid && check1 && check2);
    calculerGainVoyageur();
}

function ouvrirModalExpediteur() {
    const nom = document.getElementById('exp-nom').value;
    const prenom = document.getElementById('exp-prenom').value;
    const poids = parseFloat(document.getElementById('exp-poids').value);
    const prix = poids * 10;
    const commission = poids * 0.2;
    const total = prix + commission;

    document.getElementById('exp-confirmation-details').innerHTML = `
        <p><strong>Nom :</strong> ${nom} ${prenom}</p>
        <p><strong>Trajet :</strong> ${document.getElementById('exp-ville').value} → ${document.getElementById('exp-ville-dest').value}</p>
        <p><strong>Poids :</strong> ${poids} kg</p>
        <p><strong>Prix :</strong> ${prix.toFixed(2)} €</p>
        <p><strong>Commission :</strong> ${commission.toFixed(2)} €</p>
        <p><strong>Total :</strong> ${total.toFixed(2)} €</p>
    `;
    document.getElementById('expediteur-modal').style.display = 'flex';
}

function ouvrirModalVoyageur() {
    const nom = document.getElementById('voy-nom').value;
    const prenom = document.getElementById('voy-prenom').value;
    const poids = parseFloat(document.getElementById('voy-poids').value) || 0;
    const match = JSON.parse(localStorage.getItem('match_data') || '{}');

    // ✅ Titre et bouton selon mode
    const modalTitle = document.querySelector('#voyageur-modal .modal-title');
    const btnConfirm = document.getElementById('modal-voy-confirm');
    if (modalTitle) modalTitle.textContent = match.type === 'voyageur'
        ? 'Confirmer le matching du trajet' : 'Confirmer la publication de votre trajet';
    if (btnConfirm) btnConfirm.textContent = match.type === 'voyageur'
        ? 'Confirmer le matching' : 'Publier mon trajet';

    document.getElementById('voy-confirmation-details').innerHTML = `
        <p><strong>Nom :</strong> ${nom} ${prenom}</p>
        <p><strong>Trajet :</strong> ${document.getElementById('voy-ville-depart').value} → ${document.getElementById('voy-ville-destination').value}</p>
        <p><strong>Poids :</strong> ${poids} kg</p>
        <p><strong>Gain estimé :</strong> ${(poids * 10).toFixed(2)} €</p>
    `;
    document.getElementById('voyageur-modal').style.display = 'flex';
}

function verifierModalExpediteur() {
    const c1 = document.getElementById('modal-exp-check1').checked;
    const c2 = document.getElementById('modal-exp-check2').checked;
    document.getElementById('modal-exp-confirm').disabled = !(c1 && c2);
}

function verifierModalVoyageur() {
    const c1 = document.getElementById('modal-voy-check1').checked;
    const c2 = document.getElementById('modal-voy-check2').checked;
    document.getElementById('modal-voy-confirm').disabled = !(c1 && c2);
}

function closeModal(type) {
    document.getElementById(type + '-modal').style.display = 'none';
}

function verifierAcceptation(id) {
    const c1 = document.getElementById(`check1-${id}`)?.checked;
    const c2 = document.getElementById(`check2-${id}`)?.checked;
    const btn = document.getElementById(`btn-${id}`);
    if (btn) btn.disabled = !(c1 && c2);
}

function accepterDemande(demandeId) {
    if (!confirm("Confirmer l'acceptation ?")) return;
    fetch('/accepter-demande/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `demande_id=${demandeId}`
    }).then(r => r.json()).then(d => { if (d.status === 'ok') { showAlert("✅ Acceptée", "success"); location.reload(); } });
}

function refuserDemande(demandeId) {
    if (!confirm("Confirmer le refus ?")) return;
    fetch('/refuser-demande/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `demande_id=${demandeId}`
    }).then(r => r.json()).then(d => { if (d.status === 'ok') { showAlert("❌ Refusée", "success"); location.reload(); } });
}

function choisirType(type) {
    const input = document.getElementById('type_profil');
    if (input) input.value = type;
    document.querySelectorAll('.choice-btn').forEach(btn => btn.classList.remove('selected'));
    if (type === 'voyageur') document.querySelectorAll('.choice-btn')[0]?.classList.add('selected');
    else document.querySelectorAll('.choice-btn')[1]?.classList.add('selected');
}

// ================================================================
// ✅ SYSTÈME LANGUE — Traduction complète sans rechargement
// ================================================================

const TRADUCTIONS = {
    fr: {
        // Navigation
        menu_toutes: 'Toutes',
        voyageurs_dispo: 'Voyageurs disponibles',
        expediteurs_dispo: 'Expéditeurs disponibles',
        recherche_placeholder: 'Rechercher un trajet, une ville...',
        nav_accueil: 'Accueil',
        nav_expedier: 'Expédier',
        nav_voyager: 'Voyager',
        nav_profil: 'Profil',
        // Page accueil
        hero_titre: 'Lien sûr entre vos bagages et vos colis',
        hero_sous_titre: 'Trouvez un voyageur pour transporter vos colis partout dans le monde',
        section_voyageurs: '🛄 Voyageurs disponibles',
        section_expediteurs: '📦 Expéditeurs disponibles',
        btn_selectionner: 'Sélectionner',
        btn_complet: 'Complet',
        kg_disponibles: 'disponibles',
        a_transporter: 'à transporter',
        prix_pour_vous: '10€/kg pour vous',
        aucun_voyageur: 'Aucun voyageur disponible',
        aucun_expediteur: 'Aucun expéditeur disponible',
        // Formulaires
        form_nom: 'Nom *',
        form_prenom: 'Prénom *',
        form_telephone: 'Téléphone *',
        form_pays: 'Pays *',
        form_ville: 'Ville *',
        form_pays_dest: 'Pays de destination *',
        form_ville_dest: 'Ville de destination *',
        form_poids: 'Poids du colis (kg) *',
        form_total: 'Total à payer:',
        btn_publier_demande: 'Publier ma demande',
        btn_publier_trajet: 'Publier mon trajet',
        btn_accepter_trajet: 'Accepter le trajet',
        btn_accepter_demande: 'Accepter sa demande',
        paiement_titre: 'Choisissez votre moyen de paiement *',
        // Profil
        profil_titre: 'Créer votre profil',
        profil_etes_vous: 'ÊTES-VOUS ?',
        profil_voyageur: '🧳 Voyageur',
        profil_expediteur: '📦 Expéditeur',
        profil_nom_complet: 'Nom complet *',
        profil_username: "Nom d'utilisateur *",
        profil_email: 'Email *',
        profil_password: 'Mot de passe *',
        profil_confirmer: 'Confirmer *',
        btn_inscrire: "S'inscrire",
        btn_connecter: 'Se connecter',
        ou_inscrire_manuellement: 'ou s\'inscrire manuellement',
        // Connexion
        connexion_titre: '🔑 Connexion',
        connexion_identifiant: "Nom d'utilisateur ou Email",
        connexion_mdp: 'Mot de passe',
        pas_de_compte: 'Pas encore de compte ?',
        // Modal connexion Google
        modal_rejoindre: 'Rejoignez KERALINK en tant que',
        modal_continuer: 'Continuer avec Google',
        modal_inscrire_manuellement: '✍️ S\'inscrire manuellement',
        modal_deja_compte: '🔑 J\'ai déjà un compte',
        modal_connecter_google: 'Se connecter avec Google',
        // Gain type
        kg_entier: 'En entier',
        kg_detail: 'En détail',
        depart: 'Départ',
        arrivee: 'Arrivée',
        colis: 'Colis',
        poids_disponible: 'Poids disponible',
        vous_recevrez: 'Vous recevrez :',
        date_depart: 'Date de départ *',
        heure_depart: 'Heure de départ *',
        date_arrivee: "Date d'arrivée *",
        heure_arrivee: "Heure d'arrivée *",
        type_kg: 'Type de kg disponible *',
        kg_entier_desc: 'Kg en entier (tout ou rien)',
        kg_detail_desc: 'Kg en détail (fractionnable)',
    },
    en: {
        // Navigation
        menu_toutes: 'All',
        voyageurs_dispo: 'Available Travelers',
        expediteurs_dispo: 'Available Senders',
        recherche_placeholder: 'Search a route, a city...',
        nav_accueil: 'Home',
        nav_expedier: 'Send',
        nav_voyager: 'Travel',
        nav_profil: 'Profile',
        // Page accueil
        hero_titre: 'Safe link between your luggage and your parcels',
        hero_sous_titre: 'Find a traveler to transport your parcels anywhere in the world',
        section_voyageurs: '🛄 Available Travelers',
        section_expediteurs: '📦 Available Senders',
        btn_selectionner: 'Select',
        btn_complet: 'Full',
        kg_disponibles: 'available',
        a_transporter: 'to transport',
        prix_pour_vous: '10€/kg for you',
        aucun_voyageur: 'No travelers available',
        aucun_expediteur: 'No senders available',
        // Formulaires
        form_nom: 'Last Name *',
        form_prenom: 'First Name *',
        form_telephone: 'Phone *',
        form_pays: 'Country *',
        form_ville: 'City *',
        form_pays_dest: 'Destination Country *',
        form_ville_dest: 'Destination City *',
        form_poids: 'Package Weight (kg) *',
        form_total: 'Total to pay:',
        btn_publier_demande: 'Publish my request',
        btn_publier_trajet: 'Publish my route',
        btn_accepter_trajet: 'Accept the route',
        btn_accepter_demande: 'Accept the request',
        paiement_titre: 'Choose your payment method *',
        // Profil
        profil_titre: 'Create your profile',
        profil_etes_vous: 'ARE YOU A ?',
        profil_voyageur: '🧳 Traveler',
        profil_expediteur: '📦 Sender',
        profil_nom_complet: 'Full name *',
        profil_username: 'Username *',
        profil_email: 'Email *',
        profil_password: 'Password *',
        profil_confirmer: 'Confirm *',
        btn_inscrire: 'Sign Up',
        btn_connecter: 'Log In',
        ou_inscrire_manuellement: 'or sign up manually',
        // Connexion
        connexion_titre: '🔑 Login',
        connexion_identifiant: 'Username or Email',
        connexion_mdp: 'Password',
        pas_de_compte: 'No account yet?',
        // Modal connexion Google
        modal_rejoindre: 'Join KERALINK as a',
        modal_continuer: 'Continue with Google',
        modal_inscrire_manuellement: '✍️ Sign up manually',
        modal_deja_compte: '🔑 I already have an account',
        modal_connecter_google: 'Sign in with Google',
        // Gain type
        kg_entier: 'Whole',
        kg_detail: 'Detailed',
        depart: 'Departure',
        arrivee: 'Arrival',
        colis: 'Package',
        poids_disponible: 'Available weight',
        vous_recevrez: 'You will receive:',
        date_depart: 'Departure date *',
        heure_depart: 'Departure time *',
        date_arrivee: 'Arrival date *',
        heure_arrivee: 'Arrival time *',
        type_kg: 'Available kg type *',
        kg_entier_desc: 'Whole kg (all or nothing)',
        kg_detail_desc: 'Detailed kg (fractional)',
    }
};

let langueActuelle = localStorage.getItem('keralink_langue') || 'fr';

function setLangue(code) {
    langueActuelle = code;
    localStorage.setItem('keralink_langue', code);

    // Mettre à jour le bouton
    const flags = { fr: '🇫🇷', en: '🇬🇧' };
    const labels = { fr: 'FR', en: 'EN' };
    const flagEl = document.getElementById('lang-flag');
    const labelEl = document.getElementById('lang-label');
    if (flagEl) flagEl.textContent = flags[code] || '🇫🇷';
    if (labelEl) labelEl.textContent = labels[code] || 'FR';

    // Traduire tous les éléments data-i18n
    _appliquerTraductions();
    // Fermer le menu
    document.getElementById('lang-menu').style.display = 'none';
}

function _appliquerTraductions() {
    const t = TRADUCTIONS[langueActuelle] || TRADUCTIONS.fr;

    // Textes data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) el.textContent = t[key];
    });

    // Placeholders data-i18n-placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (t[key]) el.placeholder = t[key];
    });
}

function toggleLangMenu() {
    const m = document.getElementById('lang-menu');
    const c = document.getElementById('currency-menu');
    if (c) c.style.display = 'none';
    m.style.display = m.style.display === 'block' ? 'none' : 'block';
}

// ================================================================
// ✅ SYSTÈME MONNAIE — Conversion en temps réel sans rechargement
// ================================================================

// Taux de conversion depuis EUR (base)
const TAUX_CHANGE = {
    EUR: 1,
    USD: 1.09,
    GBP: 0.86,
    XOF: 655.96,
    JPY: 163.5,
    CAD: 1.47,
    CHF: 0.98,
    MAD: 10.85,
    DZD: 146.2,
    TND: 3.38,
};

const SYMBOLES = {
    EUR: '€', USD: '$', GBP: '£', XOF: 'FCFA',
    JPY: '¥', CAD: 'CA$', CHF: 'CHF', MAD: 'MAD',
    DZD: 'DZD', TND: 'TND'
};

let monnaieActuelle = localStorage.getItem('keralink_monnaie') || 'EUR';
let tauxActuel = TAUX_CHANGE[monnaieActuelle] || 1;
let symboleActuel = SYMBOLES[monnaieActuelle] || '€';

// Prix de base en EUR (toujours conservés)
const PRIX_BASE_EUR = {
    par_kg: 10,
    commission_par_kg: 0.20,
    total_par_kg: 10.20,
};

function setMonnaie(code, symbole, label) {
    monnaieActuelle = code;
    tauxActuel = TAUX_CHANGE[code] || 1;
    symboleActuel = SYMBOLES[code] || symbole;

    localStorage.setItem('keralink_monnaie', code);

    // Mettre à jour le bouton
    const symEl = document.getElementById('currency-symbol');
    const labEl = document.getElementById('currency-label');
    if (symEl) symEl.textContent = symboleActuel;
    if (labEl) labEl.textContent = label;

    // Mettre à jour tous les prix affichés
    _mettreAJourPrix();

    // Fermer le menu
    document.getElementById('currency-menu').style.display = 'none';
}

function convertirPrix(montantEUR) {
    return (montantEUR * tauxActuel).toFixed(2);
}

function formatPrix(montantEUR) {
    const converti = convertirPrix(montantEUR);
    if (monnaieActuelle === 'XOF' || monnaieActuelle === 'JPY') {
        return Math.round(montantEUR * tauxActuel) + ' ' + symboleActuel;
    }
    return converti + ' ' + symboleActuel;
}

function _mettreAJourPrix() {
    // ✅ Mettre à jour les prix affichés sur les cartes voyageurs/expéditeurs
    document.querySelectorAll('[data-prix-eur]').forEach(el => {
        const eur = parseFloat(el.getAttribute('data-prix-eur'));
        if (!isNaN(eur)) el.textContent = formatPrix(eur);
    });

    // ✅ Mettre à jour le total du formulaire expéditeur si rempli
    const poidsExpEl = document.getElementById('exp-poids');
    if (poidsExpEl && poidsExpEl.value) {
        const poids = parseFloat(poidsExpEl.value);
        if (!isNaN(poids) && poids > 0) {
            const totalEl = document.getElementById('exp-total');
            if (totalEl) totalEl.textContent = formatPrix(poids * PRIX_BASE_EUR.par_kg);
        }
    }

    // ✅ Mettre à jour le gain du formulaire voyageur si rempli
    const poidsVoyEl = document.getElementById('voy-poids');
    if (poidsVoyEl && poidsVoyEl.value) {
        const poids = parseFloat(poidsVoyEl.value);
        if (!isNaN(poids) && poids > 0) {
            const gainEl = document.getElementById('voy-gain');
            if (gainEl) gainEl.textContent = formatPrix(poids * PRIX_BASE_EUR.par_kg);
        }
    }

    // ✅ Mettre à jour les textes "10€/kg pour vous" sur les cartes
    document.querySelectorAll('[data-prix-kg]').forEach(el => {
        const texteBase = langueActuelle === 'en' ? 'for you' : 'pour vous';
        el.textContent = formatPrix(PRIX_BASE_EUR.par_kg) + '/kg ' + texteBase;
    });
}

function toggleCurrencyMenu() {
    const m = document.getElementById('currency-menu');
    const l = document.getElementById('lang-menu');
    if (l) l.style.display = 'none';
    m.style.display = m.style.display === 'block' ? 'none' : 'block';
}

// Fermer les menus en cliquant ailleurs
document.addEventListener('click', (e) => {
    if (!e.target.closest('.lang-selector')) {
        const m = document.getElementById('lang-menu');
        if (m) m.style.display = 'none';
    }
    if (!e.target.closest('.currency-selector')) {
        const m = document.getElementById('currency-menu');
        if (m) m.style.display = 'none';
    }
});

// ✅ Remplacer calculerPrixExpediteur pour prendre en compte la monnaie
function calculerPrixExpediteur() {
    const poids = parseFloat(document.getElementById('exp-poids').value);
    if (!isNaN(poids) && poids > 0) {
        document.getElementById('exp-total').textContent = formatPrix(poids * PRIX_BASE_EUR.par_kg);
    } else {
        document.getElementById('exp-total').textContent = formatPrix(0);
    }
    verifierFormulaireExpediteur();
}

// ✅ Remplacer calculerGainVoyageur pour prendre en compte la monnaie
function calculerGainVoyageur() {
    const poids = parseFloat(document.getElementById('voy-poids').value);
    const gainEl = document.getElementById('voy-gain');
    if (gainEl) {
        gainEl.textContent = (!isNaN(poids) && poids > 0) ? formatPrix(poids * PRIX_BASE_EUR.par_kg) : formatPrix(0);
    }
}

// ✅ Initialisation au chargement
document.addEventListener('DOMContentLoaded', function () {
    // Appliquer langue sauvegardée
    setLangue(langueActuelle);
    // Appliquer monnaie sauvegardée
    setMonnaie(monnaieActuelle, symboleActuel, monnaieActuelle);
});

// ================================================================
// ✅ INDICATEURS TÉLÉPHONIQUES
// ================================================================

const INDICATIFS_PAYS = [
    { code: '+33', pays: 'France', flag: '🇫🇷' },
    { code: '+32', pays: 'Belgique', flag: '🇧🇪' },
    { code: '+41', pays: 'Suisse', flag: '🇨🇭' },
    { code: '+352', pays: 'Luxembourg', flag: '🇱🇺' },
    { code: '+1', pays: 'USA / Canada', flag: '🇺🇸' },
    { code: '+44', pays: 'Royaume-Uni', flag: '🇬🇧' },
    { code: '+49', pays: 'Allemagne', flag: '🇩🇪' },
    { code: '+34', pays: 'Espagne', flag: '🇪🇸' },
    { code: '+39', pays: 'Italie', flag: '🇮🇹' },
    { code: '+351', pays: 'Portugal', flag: '🇵🇹' },
    { code: '+31', pays: 'Pays-Bas', flag: '🇳🇱' },
    { code: '+46', pays: 'Suède', flag: '🇸🇪' },
    { code: '+47', pays: 'Norvège', flag: '🇳🇴' },
    { code: '+45', pays: 'Danemark', flag: '🇩🇰' },
    { code: '+358', pays: 'Finlande', flag: '🇫🇮' },
    { code: '+48', pays: 'Pologne', flag: '🇵🇱' },
    { code: '+7', pays: 'Russie', flag: '🇷🇺' },
    { code: '+237', pays: 'Cameroun', flag: '🇨🇲' },
    { code: '+225', pays: 'Côte d\'Ivoire', flag: '🇨🇮' },
    { code: '+221', pays: 'Sénégal', flag: '🇸🇳' },
    { code: '+223', pays: 'Mali', flag: '🇲🇱' },
    { code: '+226', pays: 'Burkina Faso', flag: '🇧🇫' },
    { code: '+228', pays: 'Togo', flag: '🇹🇬' },
    { code: '+229', pays: 'Bénin', flag: '🇧🇯' },
    { code: '+224', pays: 'Guinée', flag: '🇬🇳' },
    { code: '+245', pays: 'Guinée-Bissau', flag: '🇬🇼' },
    { code: '+236', pays: 'RCA', flag: '🇨🇫' },
    { code: '+241', pays: 'Gabon', flag: '🇬🇦' },
    { code: '+242', pays: 'Congo', flag: '🇨🇬' },
    { code: '+243', pays: 'RDC', flag: '🇨🇩' },
    { code: '+240', pays: 'Guinée Éq.', flag: '🇬🇶' },
    { code: '+235', pays: 'Tchad', flag: '🇹🇩' },
    { code: '+216', pays: 'Tunisie', flag: '🇹🇳' },
    { code: '+212', pays: 'Maroc', flag: '🇲🇦' },
    { code: '+213', pays: 'Algérie', flag: '🇩🇿' },
    { code: '+218', pays: 'Libye', flag: '🇱🇾' },
    { code: '+20', pays: 'Égypte', flag: '🇪🇬' },
    { code: '+234', pays: 'Nigeria', flag: '🇳🇬' },
    { code: '+233', pays: 'Ghana', flag: '🇬🇭' },
    { code: '+27', pays: 'Afrique du Sud', flag: '🇿🇦' },
    { code: '+254', pays: 'Kenya', flag: '🇰🇪' },
    { code: '+255', pays: 'Tanzanie', flag: '🇹🇿' },
    { code: '+256', pays: 'Ouganda', flag: '🇺🇬' },
    { code: '+251', pays: 'Éthiopie', flag: '🇪🇹' },
    { code: '+250', pays: 'Rwanda', flag: '🇷🇼' },
    { code: '+261', pays: 'Madagascar', flag: '🇲🇬' },
    { code: '+262', pays: 'Réunion/Mayotte', flag: '🇷🇪' },
    { code: '+230', pays: 'Maurice', flag: '🇲🇺' },
    { code: '+269', pays: 'Comores', flag: '🇰🇲' },
    { code: '+86', pays: 'Chine', flag: '🇨🇳' },
    { code: '+81', pays: 'Japon', flag: '🇯🇵' },
    { code: '+82', pays: 'Corée du Sud', flag: '🇰🇷' },
    { code: '+91', pays: 'Inde', flag: '🇮🇳' },
    { code: '+92', pays: 'Pakistan', flag: '🇵🇰' },
    { code: '+880', pays: 'Bangladesh', flag: '🇧🇩' },
    { code: '+66', pays: 'Thaïlande', flag: '🇹🇭' },
    { code: '+84', pays: 'Vietnam', flag: '🇻🇳' },
    { code: '+62', pays: 'Indonésie', flag: '🇮🇩' },
    { code: '+60', pays: 'Malaisie', flag: '🇲🇾' },
    { code: '+63', pays: 'Philippines', flag: '🇵🇭' },
    { code: '+65', pays: 'Singapour', flag: '🇸🇬' },
    { code: '+966', pays: 'Arabie Saoudite', flag: '🇸🇦' },
    { code: '+971', pays: 'Émirats Arabes', flag: '🇦🇪' },
    { code: '+972', pays: 'Israël', flag: '🇮🇱' },
    { code: '+90', pays: 'Turquie', flag: '🇹🇷' },
    { code: '+55', pays: 'Brésil', flag: '🇧🇷' },
    { code: '+54', pays: 'Argentine', flag: '🇦🇷' },
    { code: '+52', pays: 'Mexique', flag: '🇲🇽' },
    { code: '+57', pays: 'Colombie', flag: '🇨🇴' },
    { code: '+51', pays: 'Pérou', flag: '🇵🇪' },
    { code: '+56', pays: 'Chili', flag: '🇨🇱' },
    { code: '+58', pays: 'Venezuela', flag: '🇻🇪' },
    { code: '+61', pays: 'Australie', flag: '🇦🇺' },
    { code: '+64', pays: 'Nouvelle-Zélande', flag: '🇳🇿' },
];

/**
 * ✅ Crée un widget indicatif téléphonique et l'insère avant l'input
 * @param {string} inputId - ID de l'input téléphone
 * @param {string} defaultCode - Code par défaut (+33 par exemple)
 */
function creerIndicatifTel(inputId, defaultCode) {
    const input = document.getElementById(inputId);
    // ✅ Vérifier que l'input existe ET n'a pas déjà été traité
    if (!input || input.closest('.indicatif-wrap')) return;

    const defIndicatif = INDICATIFS_PAYS.find(i => i.code === defaultCode) || INDICATIFS_PAYS[0];

    // Wrapper global
    const wrap = document.createElement('div');
    wrap.className = 'indicatif-wrap';
    wrap.style.cssText = 'display:flex;width:100%;';

    // Conteneur relatif pour le bouton + dropdown
    const relative = document.createElement('div');
    relative.style.cssText = 'position:relative;flex-shrink:0;';

    // Bouton indicatif
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'indicatif-btn';
    btn.setAttribute('data-code', defIndicatif.code);
    btn.style.cssText = `
        display:flex;align-items:center;gap:5px;padding:0 10px;
        background:white;border:1.5px solid #e0e0e0;border-right:none;
        border-radius:8px 0 0 8px;cursor:pointer;font-size:0.88rem;
        white-space:nowrap;height:100%;min-height:42px;min-width:85px;
        transition:background 0.15s;
    `;
    btn.innerHTML = `<span class="ind-flag">${defIndicatif.flag}</span><span class="ind-code">${defIndicatif.code}</span><span style="font-size:0.7rem;color:#aaa;margin-left:2px;">▾</span>`;

    // Dropdown
    const dropdown = document.createElement('div');
    dropdown.className = 'indicatif-dropdown';
    dropdown.style.cssText = `
        display:none;position:absolute;top:100%;left:0;z-index:99999;
        background:white;border:1.5px solid #ddd;border-radius:8px;
        box-shadow:0 8px 24px rgba(0,0,0,0.15);
        max-height:260px;overflow-y:auto;min-width:230px;
    `;

    // Recherche
    const searchInp = document.createElement('input');
    searchInp.type = 'text';
    searchInp.placeholder = 'Rechercher un pays...';
    searchInp.style.cssText = `
        width:100%;padding:9px 12px;border:none;border-bottom:1px solid #eee;
        outline:none;font-size:0.85rem;box-sizing:border-box;border-radius:8px 8px 0 0;
    `;

    const liste = document.createElement('div');

    function remplirListe(filtre) {
        liste.innerHTML = '';
        INDICATIFS_PAYS
            .filter(i => !filtre ||
                i.pays.toLowerCase().includes(filtre.toLowerCase()) ||
                i.code.includes(filtre))
            .forEach(indicatif => {
                const item = document.createElement('div');
                item.style.cssText = `padding:9px 14px;cursor:pointer;font-size:0.87rem;display:flex;align-items:center;gap:10px;transition:background 0.1s;`;
                item.innerHTML = `<span>${indicatif.flag}</span><span style="flex:1;">${indicatif.pays}</span><span style="color:#888;font-size:0.82rem;">${indicatif.code}</span>`;
                item.onmouseover = () => item.style.background = '#f5f5f5';
                item.onmouseout = () => item.style.background = 'white';
                item.onclick = (e) => {
                    e.stopPropagation();
                    btn.querySelector('.ind-code').textContent = indicatif.code;
                    btn.querySelector('.ind-flag').textContent = indicatif.flag;
                    btn.setAttribute('data-code', indicatif.code);
                    dropdown.style.display = 'none';
                    // ✅ Focus sur l'input ORIGINAL (pas un clone)
                    input.focus();
                };
                liste.appendChild(item);
            });
    }

    searchInp.addEventListener('input', () => remplirListe(searchInp.value));
    searchInp.addEventListener('click', e => e.stopPropagation());
    remplirListe('');

    dropdown.appendChild(searchInp);
    dropdown.appendChild(liste);

    btn.onclick = (e) => {
        e.stopPropagation();
        // Fermer tous les autres dropdowns ouverts
        document.querySelectorAll('.indicatif-dropdown').forEach(d => {
            if (d !== dropdown) d.style.display = 'none';
        });
        const isOpen = dropdown.style.display === 'block';
        dropdown.style.display = isOpen ? 'none' : 'block';
        if (!isOpen) setTimeout(() => searchInp.focus(), 50);
    };

    btn.onmouseover = () => btn.style.background = '#f9f9f9';
    btn.onmouseout = () => btn.style.background = 'white';

    relative.appendChild(btn);
    relative.appendChild(dropdown);

    // ✅ FIX DOUBLON : insérer le wrapper AVANT l'input original
    // puis déplacer l'input DANS le wrapper (pas de clone)
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(relative);
    wrap.appendChild(input); // ← déplace l'input existant, pas de copie

    // Adapter le style de l'input
    input.style.borderRadius = '0 8px 8px 0';
    input.style.borderLeft = 'none';
    input.style.flex = '1';
    input.style.width = '100%';
    input.placeholder = 'Numéro de téléphone';
}

// ✅ Initialiser les indicatifs sur tous les champs téléphone
function initialiserIndicatifs() {
    const champsPhone = [
        { id: 'exp-telephone', default: '+33' },
        { id: 'voy-telephone', default: '+33' },
        { id: 'telephone', default: '+33' }, // Page profil
    ];
    champsPhone.forEach(({ id, default: def }) => {
        if (document.getElementById(id)) {
            creerIndicatifTel(id, def);
        }
    });
}

// ================================================================
// ✅ VILLES PAR PAYS — Autocomplétion
// ================================================================

const VILLES_PAR_PAYS = {
    'france': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 'Montpellier', 'Bordeaux', 'Lille', 'Rennes', 'Reims', 'Le Havre', 'Saint-Étienne', 'Toulon', 'Grenoble', 'Dijon', 'Angers', 'Nîmes', 'Villeurbanne'],
    'belgique': ['Bruxelles', 'Anvers', 'Gand', 'Charleroi', 'Liège', 'Bruges', 'Namur', 'Leuven', 'Mons', 'Hasselt'],
    'suisse': ['Zurich', 'Genève', 'Berne', 'Lausanne', 'Bâle', 'Winterthour', 'Lucerne', 'Saint-Gall', 'Lugano', 'Bienne'],
    'allemagne': ['Berlin', 'Hambourg', 'Munich', 'Cologne', 'Francfort', 'Stuttgart', 'Düsseldorf', 'Dortmund', 'Essen', 'Leipzig', 'Brême', 'Dresde', 'Hanovre', 'Nuremberg'],
    'espagne': ['Madrid', 'Barcelone', 'Valence', 'Séville', 'Saragosse', 'Málaga', 'Murcie', 'Palma', 'Las Palmas', 'Bilbao', 'Alicante', 'Córdoba', 'Valladolid', 'Vigo'],
    'italie': ['Rome', 'Milan', 'Naples', 'Turin', 'Palerme', 'Gênes', 'Bologne', 'Florence', 'Bari', 'Catane', 'Venise', 'Vérone', 'Messine', 'Trieste'],
    'portugal': ['Lisbonne', 'Porto', 'Amadora', 'Braga', 'Setúbal', 'Coimbra', 'Funchal', 'Almada', 'Aveiro', 'Guimarães'],
    'royaume-uni': ['Londres', 'Birmingham', 'Manchester', 'Glasgow', 'Liverpool', 'Bristol', 'Sheffield', 'Leeds', 'Edinburgh', 'Leicester', 'Coventry', 'Bradford', 'Cardiff', 'Belfast'],
    'cameroun': ['Yaoundé', 'Douala', 'Garoua', 'Bamenda', 'Maroua', 'Bafoussam', 'Ngaoundéré', 'Bertoua', 'Loum', 'Kumba', 'Nkongsamba', 'Edéa', 'Limbé', 'Ebolowa'],
    "cote d'ivoire": ['Abidjan', 'Bouaké', 'Daloa', 'Yamoussoukro', 'Korhogo', 'San-Pédro', 'Man', 'Divo', 'Gagnoa', 'Abengourou'],
    'senegal': ['Dakar', 'Touba', 'Thiès', 'Rufisque', 'Kaolack', 'Ziguinchor', 'Saint-Louis', 'Mbour', 'Tambacounda', 'Kolda'],
    'mali': ['Bamako', 'Sikasso', 'Mopti', 'Koutiala', 'Kayes', 'Ségou', 'Gao', 'Kati', 'Tombouctou', 'Djenné'],
    'ghana': ['Accra', 'Kumasi', 'Tamale', 'Sekondi-Takoradi', 'Sunyani', 'Cape Coast', 'Koforidua', 'Ho', 'Wa', 'Bolgatanga'],
    'nigeria': ['Lagos', 'Kano', 'Ibadan', 'Kaduna', 'Port Harcourt', 'Benin City', 'Maiduguri', 'Abuja', 'Zaria', 'Aba', 'Enugu', 'Onitsha'],
    'tunisie': ['Tunis', 'Sfax', 'Sousse', 'Kairouan', 'Bizerte', 'Gabès', 'Ariana', 'Gafsa', 'Monastir', 'Ben Arous', 'Médenine', 'Nabeul'],
    'maroc': ['Casablanca', 'Rabat', 'Fès', 'Marrakech', 'Agadir', 'Tanger', 'Meknès', 'Oujda', 'Kénitra', 'Tétouan', 'Salé', 'Nador', 'Berrechid', 'Khémisset'],
    'algerie': ['Alger', 'Oran', 'Constantine', 'Annaba', 'Blida', 'Batna', 'Djelfa', 'Sétif', 'Sidi Bel Abbès', 'Biskra', 'Béjaïa', 'Tébessa', 'Tlemcen', 'Skikda'],
    'egypte': ['Le Caire', 'Alexandrie', 'Gizeh', 'Shubra El Kheima', 'Port Saïd', 'Suez', 'Louxor', 'Mansoura', 'Assouan', 'Tanta', 'Asyut', 'Ismaïlia'],
    'rdcongo': ['Kinshasa', 'Lubumbashi', 'Mbuji-Mayi', 'Goma', 'Bukavu', 'Kisangani', 'Kananga', 'Likasi', 'Kolwezi', 'Matadi'],
    'usa': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San José', 'Miami', 'Atlanta', 'Boston', 'Seattle', 'Washington DC'],
    'canada': ['Toronto', 'Montréal', 'Vancouver', 'Calgary', 'Edmonton', 'Ottawa', 'Winnipeg', 'Québec', 'Hamilton', 'Kitchener'],
    'bresil': ['São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Fortaleza', 'Belo Horizonte', 'Manaus', 'Curitiba', 'Recife', 'Porto Alegre'],
    'chine': ['Shanghai', 'Pékin', 'Chongqing', 'Guangzhou', 'Shenzhen', 'Chengdu', 'Tianjin', 'Wuhan', 'Dongguan', 'Nanjing', 'Hong Kong', 'Hangzhou', 'Xi\'an'],
    'inde': ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Ahmedabad', 'Chennai', 'Kolkata', 'Surat', 'Pune', 'Jaipur', 'Lucknow', 'Kanpur'],
    'japon': ['Tokyo', 'Osaka', 'Nagoya', 'Sapporo', 'Fukuoka', 'Kobe', 'Kyoto', 'Kawasaki', 'Hiroshima', 'Sendai', 'Yokohama'],
    'emirats arabes': ['Dubaï', 'Abu Dhabi', 'Sharjah', 'Al Ain', 'Ajman', 'Ras Al Khaimah', 'Fujairah', 'Umm Al Quwain'],
    'arabie saoudite': ['Riyad', 'Djeddah', 'La Mecque', 'Médine', 'Dammam', 'Taïf', 'Tabuk', 'Abha', 'Khobar', 'Najran'],
    'australie': ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide', 'Gold Coast', 'Canberra', 'Newcastle', 'Wollongong', 'Logan'],
    'mexique': ['Mexico', 'Guadalajara', 'Monterrey', 'Puebla', 'Toluca', 'Tijuana', 'Mérida', 'Acapulco', 'Juárez', 'Cancún'],
    'argentine': ['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'Tucumán', 'La Plata', 'Mar del Plata', 'Salta', 'Santa Fe', 'Neuquén'],
    'afrique du sud': ['Johannesburg', 'Cape Town', 'Durban', 'Pretoria', 'Port Elizabeth', 'Bloemfontein', 'Nelspruit', 'Kimberley', 'Polokwane'],
    'kenya': ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 'Nyeri', 'Malindi', 'Kitale', 'Garissa'],
    'gabon': ['Libreville', 'Port-Gentil', 'Franceville', 'Oyem', 'Moanda', 'Mouila', 'Lambaréné', 'Tchibanga', 'Koulamoutou', 'Makokou'],
    'congo': ['Brazzaville', 'Pointe-Noire', 'Dolisie', 'Nkayi', 'Owando', 'Ouesso', 'Impfondo', 'Sibiti', 'Madingou'],
    'ethiopie': ['Addis-Abeba', 'Dire Dawa', 'Mekelle', 'Gondär', 'Adama', 'Hawassa', 'Bahir Dar', 'Dessie', 'Jimma'],
    'madagascar': ['Antananarivo', 'Toamasina', 'Antsirabe', 'Fianarantsoa', 'Mahajanga', 'Toliara', 'Antsiranana', 'Nosy Be'],
    'turquie': ['Istanbul', 'Ankara', 'Izmir', 'Bursa', 'Adana', 'Gaziantep', 'Konya', 'Antalya', 'Kayseri', 'Trabzon'],
};

/**
 * ✅ Lie un champ pays à un champ ville avec autocomplétion
 */
function lierPaysVille(inputPaysId, inputVilleId) {
    const inputPays = document.getElementById(inputPaysId);
    const inputVille = document.getElementById(inputVilleId);
    if (!inputPays || !inputVille) return;

    // Créer dropdown de villes
    const wrapper = document.createElement('div');
    wrapper.style.cssText = 'position:relative;flex:1;';

    inputVille.style.width = '100%';
    inputVille.parentNode.insertBefore(wrapper, inputVille);
    wrapper.appendChild(inputVille);

    const dropdown = document.createElement('div');
    dropdown.style.cssText = `
        display:none;position:absolute;top:100%;left:0;right:0;z-index:9999;
        background:white;border:1px solid #ddd;border-radius:8px;
        box-shadow:0 8px 24px rgba(0,0,0,0.15);
        max-height:220px;overflow-y:auto;
    `;
    wrapper.appendChild(dropdown);

    function normaliserPays(pays) {
        return pays.toLowerCase()
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-z0-9\s']/g, '')
            .trim();
    }

    function afficherVilles(filtre) {
        const paysNorm = normaliserPays(inputPays.value);
        let villes = [];

        // Chercher une correspondance
        for (const [key, vals] of Object.entries(VILLES_PAR_PAYS)) {
            if (paysNorm.includes(key) || key.includes(paysNorm)) {
                villes = vals;
                break;
            }
        }

        if (!villes.length) { dropdown.style.display = 'none'; return; }

        const filtered = filtre
            ? villes.filter(v => v.toLowerCase().includes(filtre.toLowerCase()))
            : villes;

        if (!filtered.length) { dropdown.style.display = 'none'; return; }

        dropdown.innerHTML = '';
        filtered.forEach(ville => {
            const item = document.createElement('div');
            item.style.cssText = `
                padding:9px 14px;cursor:pointer;font-size:0.88rem;
                transition:background 0.1s;
            `;
            item.textContent = ville;
            item.onmouseover = () => item.style.background = '#f5f5f5';
            item.onmouseout = () => item.style.background = 'white';
            item.onclick = () => {
                inputVille.value = ville;
                dropdown.style.display = 'none';
                // Déclencher vérification formulaire
                inputVille.dispatchEvent(new Event('input'));
            };
            dropdown.appendChild(item);
        });
        dropdown.style.display = 'block';
    }

    // Afficher les villes quand on clique sur le champ ville
    inputVille.addEventListener('focus', () => afficherVilles(inputVille.value));
    inputVille.addEventListener('input', () => afficherVilles(inputVille.value));

    // Fermer dropdown si on clique ailleurs
    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) dropdown.style.display = 'none';
    });

    // Re-déclencher quand le pays change
    inputPays.addEventListener('input', () => {
        inputVille.value = '';
        dropdown.style.display = 'none';
    });
    inputPays.addEventListener('blur', () => {
        setTimeout(() => afficherVilles(''), 200);
    });
}

// ✅ Initialiser toutes les liaisons pays→ville
function initialiserPaysVille() {
    // Formulaire expéditeur
    lierPaysVille('exp-pays', 'exp-ville');
    lierPaysVille('exp-pays-dest', 'exp-ville-dest');
    // Formulaire voyageur
    lierPaysVille('voy-pays-depart', 'voy-ville-depart');
    lierPaysVille('voy-pays-destination', 'voy-ville-destination');
}

// ================================================================
// ✅ PAGES FOOTER — Comment ça marche, Tarifs, Contact
// ================================================================

function ouvrirCommentCaMarche() {
    const existant = document.getElementById('modal-comment');
    if (existant) { existant.remove(); return; }

    const modal = _creerModalFooter('modal-comment');
    modal.innerHTML = `
        <div style="background:white;border-radius:16px;max-width:700px;width:94%;
                    max-height:88vh;overflow-y:auto;box-shadow:0 24px 64px rgba(0,0,0,0.35);">
            <div style="background:linear-gradient(120deg,#0A1F44,#1E3A8A);padding:24px 28px;
                        border-radius:16px 16px 0 0;display:flex;justify-content:space-between;align-items:center;
                        position:sticky;top:0;z-index:1;">
                <div>
                    <h2 style="color:white;font-size:1.2rem;margin-bottom:4px;">🚀 Comment ça marche ?</h2>
                    <p style="color:#a0cfff;font-size:0.82rem;">Envoyez vos colis simplement avec KERALINK</p>
                </div>
                <button onclick="document.getElementById('modal-comment').remove()"
                        style="background:rgba(255,255,255,0.2);border:none;color:white;
                               width:36px;height:36px;border-radius:50%;font-size:1.3rem;cursor:pointer;">×</button>
            </div>
            <div style="padding:28px;">

                <div style="display:grid;gap:20px;">

                    <div style="background:#e3f2fd;border-radius:12px;padding:20px;border-left:5px solid #1E3A8A;">
                        <div style="font-size:1.8rem;margin-bottom:8px;">📦</div>
                        <h3 style="color:#0A1F44;margin-bottom:8px;">Pour les Expéditeurs</h3>
                        <ol style="margin-left:20px;line-height:2;">
                            <li>Publiez votre demande d'expédition avec vos informations et votre colis</li>
                            <li>Choisissez un voyageur disponible sur votre trajet ou attendez d'être contacté</li>
                            <li>Effectuez le paiement sécurisé (bloqué en séquestre jusqu'à livraison)</li>
                            <li>Le voyageur transporte votre colis et vous envoie une photo de livraison</li>
                            <li>Confirmez la réception → le voyageur reçoit ses gains</li>
                        </ol>
                    </div>

                    <div style="background:#e8f5e9;border-radius:12px;padding:20px;border-left:5px solid #2e7d32;">
                        <div style="font-size:1.8rem;margin-bottom:8px;">🧳</div>
                        <h3 style="color:#0A1F44;margin-bottom:8px;">Pour les Voyageurs</h3>
                        <ol style="margin-left:20px;line-height:2;">
                            <li>Publiez votre trajet avec vos dates, destinations et espace disponible</li>
                            <li>Recevez des demandes d'expédition ou sélectionnez un expéditeur</li>
                            <li>Acceptez les demandes qui correspondent à votre trajet</li>
                            <li>Transportez le colis et prenez une photo à la livraison</li>
                            <li>Recevez vos gains dans votre portefeuille KERALINK</li>
                        </ol>
                    </div>

                    <div style="background:#fff3e0;border-radius:12px;padding:20px;border-left:5px solid #FF7A00;">
                        <div style="font-size:1.8rem;margin-bottom:8px;">🔒</div>
                        <h3 style="color:#0A1F44;margin-bottom:8px;">Sécurité & Garanties</h3>
                        <ul style="margin-left:20px;line-height:2;">
                            <li>Paiement bloqué en séquestre jusqu'à confirmation de livraison</li>
                            <li>Photo de preuve obligatoire pour valider chaque livraison</li>
                            <li>Déblocage automatique des gains après 48h si l'expéditeur ne confirme pas</li>
                            <li>Support disponible 24/7 pour tout litige</li>
                        </ul>
                    </div>

                </div>

                <div style="text-align:center;margin-top:24px;">
                    <button onclick="document.getElementById('modal-comment').remove(); showPage(null, 'expediteur')"
                            style="background:linear-gradient(90deg,#FF7A00,#e66900);color:white;border:none;
                                   padding:12px 28px;border-radius:10px;font-size:0.95rem;font-weight:bold;
                                   cursor:pointer;margin-right:10px;">
                        📦 Expédier un colis
                    </button>
                    <button onclick="document.getElementById('modal-comment').remove(); showPage(null, 'voyageur')"
                            style="background:linear-gradient(90deg,#0A1F44,#1E3A8A);color:white;border:none;
                                   padding:12px 28px;border-radius:10px;font-size:0.95rem;font-weight:bold;
                                   cursor:pointer;">
                        🧳 Proposer un trajet
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function ouvrirTarifs() {
    const existant = document.getElementById('modal-tarifs');
    if (existant) { existant.remove(); return; }

    const modal = _creerModalFooter('modal-tarifs');
    modal.innerHTML = `
        <div style="background:white;border-radius:16px;max-width:620px;width:94%;
                    max-height:88vh;overflow-y:auto;box-shadow:0 24px 64px rgba(0,0,0,0.35);">
            <div style="background:linear-gradient(120deg,#0A1F44,#1E3A8A);padding:24px 28px;
                        border-radius:16px 16px 0 0;display:flex;justify-content:space-between;align-items:center;
                        position:sticky;top:0;z-index:1;">
                <div>
                    <h2 style="color:white;font-size:1.2rem;margin-bottom:4px;">💰 Tarifs KERALINK</h2>
                    <p style="color:#a0cfff;font-size:0.82rem;">Transparence totale sur nos frais</p>
                </div>
                <button onclick="document.getElementById('modal-tarifs').remove()"
                        style="background:rgba(255,255,255,0.2);border:none;color:white;
                               width:36px;height:36px;border-radius:50%;font-size:1.3rem;cursor:pointer;">×</button>
            </div>
            <div style="padding:28px;">

                <!-- Tableau tarifs -->
                <div style="background:#f9f9f9;border-radius:12px;overflow:hidden;margin-bottom:20px;">
                    <div style="background:#0A1F44;color:white;padding:12px 20px;font-weight:bold;">
                        📋 Grille tarifaire standard
                    </div>
                    <table style="width:100%;border-collapse:collapse;">
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:14px 20px;font-size:0.92rem;">💸 Prix pour l'expéditeur</td>
                            <td style="padding:14px 20px;text-align:right;font-weight:bold;color:#FF7A00;font-size:1.1rem;">10,20 €/kg</td>
                        </tr>
                        <tr style="border-bottom:1px solid #eee;background:#fafafa;">
                            <td style="padding:14px 20px;font-size:0.92rem;">💼 Gain pour le voyageur</td>
                            <td style="padding:14px 20px;text-align:right;font-weight:bold;color:#2e7d32;font-size:1.1rem;">10,00 €/kg</td>
                        </tr>
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:14px 20px;font-size:0.92rem;">🏢 Commission KERALINK</td>
                            <td style="padding:14px 20px;text-align:right;font-weight:bold;color:#1E3A8A;">0,20 €/kg</td>
                        </tr>
                        <tr style="background:#fff3e0;">
                            <td style="padding:14px 20px;font-size:0.92rem;">↩️ Remboursement (si annulation)</td>
                            <td style="padding:14px 20px;text-align:right;font-weight:bold;color:#e65100;">10,00 €/kg</td>
                        </tr>
                    </table>
                </div>

                <!-- Exemples -->
                <h3 style="color:#0A1F44;margin-bottom:14px;">📦 Exemples concrets</h3>
                <div style="display:grid;gap:12px;margin-bottom:20px;">
                    ${[
                        { kg: 5, label: 'Petit colis (5 kg)' },
                        { kg: 10, label: 'Colis moyen (10 kg)' },
                        { kg: 23, label: 'Grande valise (23 kg)' },
                    ].map(ex => `
                        <div style="background:#f5f5f5;border-radius:10px;padding:14px 18px;
                                    display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <strong>${ex.label}</strong>
                                <div style="font-size:0.82rem;color:#888;margin-top:2px;">
                                    Voyageur : <strong style="color:#2e7d32;">${(ex.kg * 10).toFixed(2)} €</strong>
                                    &nbsp;|&nbsp; Commission : ${(ex.kg * 0.2).toFixed(2)} €
                                </div>
                            </div>
                            <div style="font-size:1.2rem;font-weight:bold;color:#FF7A00;">
                                ${(ex.kg * 10.2).toFixed(2)} €
                            </div>
                        </div>
                    `).join('')}
                </div>

                <div style="background:#e8f5e9;border-radius:10px;padding:14px;border-left:4px solid #2e7d32;font-size:0.88rem;color:#555;">
                    ✅ <strong>Aucun frais caché.</strong> La commission de 0,20€/kg est la seule retenue de la plateforme.
                    En cas de remboursement, seule la commission est non remboursable.
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function ouvrirContact() {
    const existant = document.getElementById('modal-contact');
    if (existant) { existant.remove(); return; }

    const modal = _creerModalFooter('modal-contact');
    modal.innerHTML = `
        <div style="background:white;border-radius:16px;max-width:560px;width:94%;
                    max-height:88vh;overflow-y:auto;box-shadow:0 24px 64px rgba(0,0,0,0.35);">
            <div style="background:linear-gradient(120deg,#0A1F44,#1E3A8A);padding:24px 28px;
                        border-radius:16px 16px 0 0;display:flex;justify-content:space-between;align-items:center;
                        position:sticky;top:0;z-index:1;">
                <div>
                    <h2 style="color:white;font-size:1.2rem;margin-bottom:4px;">📬 Contactez-nous</h2>
                    <p style="color:#a0cfff;font-size:0.82rem;">Notre équipe répond sous 24h</p>
                </div>
                <button onclick="document.getElementById('modal-contact').remove()"
                        style="background:rgba(255,255,255,0.2);border:none;color:white;
                               width:36px;height:36px;border-radius:50%;font-size:1.3rem;cursor:pointer;">×</button>
            </div>
            <div style="padding:28px;">

                <div style="display:grid;gap:14px;margin-bottom:24px;">
                    <div style="background:#e3f2fd;border-radius:10px;padding:16px;display:flex;align-items:center;gap:14px;">
                        <div style="font-size:2rem;">💬</div>
                        <div>
                            <strong style="color:#0A1F44;">Support intégré</strong>
                            <p style="font-size:0.85rem;color:#555;margin-top:4px;">
                                Utilisez le chat support dans votre espace personnel.
                                Disponible 7j/7, réponse sous 24h.
                            </p>
                        </div>
                    </div>

                    <div style="background:#e8f5e9;border-radius:10px;padding:16px;display:flex;align-items:center;gap:14px;">
                        <div style="font-size:2rem;">📧</div>
                        <div>
                            <strong style="color:#0A1F44;">Email</strong>
                            <p style="font-size:0.85rem;color:#555;margin-top:4px;">
                                support@keralink.com<br>
                                <span style="color:#888;">Réponse sous 24-48h ouvrées</span>
                            </p>
                        </div>
                    </div>

                    <div style="background:#fff3e0;border-radius:10px;padding:16px;display:flex;align-items:center;gap:14px;">
                        <div style="font-size:2rem;">🌍</div>
                        <div>
                            <strong style="color:#0A1F44;">Zones desservies</strong>
                            <p style="font-size:0.85rem;color:#555;margin-top:4px;">
                                Europe, Afrique, Amérique, Asie<br>
                                <span style="color:#888;">Service disponible dans le monde entier</span>
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Formulaire contact rapide -->
                <h3 style="color:#0A1F44;margin-bottom:14px;">✍️ Envoyer un message</h3>
                <div style="margin-bottom:12px;">
                    <input type="text" id="contact-nom" placeholder="Votre nom *"
                           style="width:100%;padding:11px 14px;border-radius:8px;border:1.5px solid #e0e0e0;
                                  font-size:0.9rem;outline:none;box-sizing:border-box;margin-bottom:10px;">
                    <input type="email" id="contact-email" placeholder="Votre email *"
                           style="width:100%;padding:11px 14px;border-radius:8px;border:1.5px solid #e0e0e0;
                                  font-size:0.9rem;outline:none;box-sizing:border-box;margin-bottom:10px;">
                    <select id="contact-sujet"
                            style="width:100%;padding:11px 14px;border-radius:8px;border:1.5px solid #e0e0e0;
                                   font-size:0.9rem;outline:none;background:white;box-sizing:border-box;margin-bottom:10px;">
                        <option value="">Sujet de votre message *</option>
                        <option>❓ Question générale</option>
                        <option>💳 Problème de paiement</option>
                        <option>📦 Problème de livraison</option>
                        <option>👤 Problème de compte</option>
                        <option>↩️ Demande de remboursement</option>
                        <option>🚨 Signaler un abus</option>
                        <option>💡 Suggestion</option>
                    </select>
                    <textarea id="contact-message" placeholder="Votre message *"
                              style="width:100%;padding:11px 14px;border-radius:8px;border:1.5px solid #e0e0e0;
                                     font-size:0.9rem;outline:none;resize:none;height:100px;
                                     box-sizing:border-box;font-family:inherit;"></textarea>
                </div>
                <button onclick="_envoyerContact()"
                        style="width:100%;padding:12px;border-radius:10px;
                               background:linear-gradient(90deg,#FF7A00,#e66900);
                               color:white;border:none;font-weight:bold;font-size:0.95rem;cursor:pointer;">
                    📬 Envoyer le message
                </button>

                <div id="contact-confirmation" style="display:none;margin-top:16px;
                     background:#e8f5e9;border-radius:8px;padding:14px;text-align:center;
                     color:#2e7d32;font-weight:bold;">
                    ✅ Message envoyé ! Notre équipe vous répondra sous 24h.
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function _envoyerContact() {
    const nom = document.getElementById('contact-nom')?.value.trim();
    const email = document.getElementById('contact-email')?.value.trim();
    const sujet = document.getElementById('contact-sujet')?.value;
    const message = document.getElementById('contact-message')?.value.trim();
    if (!nom || !email || !sujet || !message) {
        showAlert('⚠️ Veuillez remplir tous les champs', 'default');
        return;
    }
    // Simuler l'envoi
    document.getElementById('contact-confirmation').style.display = 'block';
    document.getElementById('contact-nom').value = '';
    document.getElementById('contact-email').value = '';
    document.getElementById('contact-sujet').value = '';
    document.getElementById('contact-message').value = '';
}

function _creerModalFooter(id) {
    const modal = document.createElement('div');
    modal.id = id;
    modal.style.cssText = `
        position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:99999;
        display:flex;align-items:center;justify-content:center;
        backdrop-filter:blur(4px);
    `;
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
    document.body.style.overflow = 'hidden';
    modal.addEventListener('remove', () => { document.body.style.overflow = ''; });
    return modal;
}

// ✅ Initialisation globale au chargement
document.addEventListener('DOMContentLoaded', function() {
    // Indicatifs téléphoniques
    initialiserIndicatifs();
    // Liaisons pays → ville
    initialiserPaysVille();
});
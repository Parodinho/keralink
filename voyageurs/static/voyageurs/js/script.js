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

// ================================================================
// ✅ AUTH — Inscription / Connexion sur Expédier & Voyager
// ================================================================

function afficherFormInscription(type) {
    const prefix = type === 'expediteur' ? 'exp' : 'voy';
    const authZone = document.getElementById(prefix + '-auth-zone');
    const formZone = document.getElementById(prefix + '-form-zone');
    const inscrire = document.getElementById(prefix + '-inscrire-form');
    const login = document.getElementById(prefix + '-login-form');

    if (authZone) authZone.style.display = 'block';
    if (formZone) formZone.style.display = 'none';
    if (inscrire) inscrire.style.display = 'block';
    if (login) login.style.display = 'none';
}

function afficherFormConnexion(type) {
    const prefix = type === 'expediteur' ? 'exp' : 'voy';
    const authZone = document.getElementById(prefix + '-auth-zone');
    const formZone = document.getElementById(prefix + '-form-zone');
    const inscrire = document.getElementById(prefix + '-inscrire-form');
    const login = document.getElementById(prefix + '-login-form');

    if (authZone) authZone.style.display = 'block';
    if (formZone) formZone.style.display = 'none';
    if (inscrire) inscrire.style.display = 'none';
    if (login) login.style.display = 'block';
}

function afficherZoneFormulaire(type) {
    const prefix = type === 'expediteur' ? 'exp' : 'voy';
    const authZone = document.getElementById(prefix + '-auth-zone');
    const formZone = document.getElementById(prefix + '-form-zone');
    if (authZone) authZone.style.display = 'none';
    if (formZone) formZone.style.display = 'block';
    if (typeof preremplirDepuisProfil === 'function') preremplirDepuisProfil();
}

function soumettreInscription(type) {
    const prefix = type === 'expediteur' ? 'exp' : 'voy';
    const nom = document.getElementById(prefix + '-reg-nom')?.value.trim() || '';
    const prenom = document.getElementById(prefix + '-reg-prenom')?.value.trim() || '';
    const username = document.getElementById(prefix + '-reg-username')?.value.trim() || '';
    const email = document.getElementById(prefix + '-reg-email')?.value.trim() || '';
    const password = document.getElementById(prefix + '-reg-password')?.value || '';
    const password2 = document.getElementById(prefix + '-reg-password2')?.value || '';

    if (!nom || !prenom || !username || !email || !password) {
        showAlert('⚠️ Veuillez remplir tous les champs', 'default');
        return;
    }
    if (password !== password2) {
        showAlert('❌ Les mots de passe ne correspondent pas', 'default');
        return;
    }

    const formData = new FormData();
    formData.append('nom', nom);
    formData.append('prenom', prenom);
    formData.append('username', username);
    formData.append('email', email);
    formData.append('password', password);
    formData.append('password2', password2);
    formData.append('type_profil', type);

    fetch('/inscrire/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            // Compte créé → afficher le formulaire de publication (PAS le dashboard)
            window.EST_CONNECTE = true;
            localStorage.setItem('profil_connecte', JSON.stringify({
                nom_complet: data.nom_complet,
                type_profil: data.type_profil,
                profil_id: data.profil_id,
                guest_id: data.guest_id
            }));
            showAlert('✅ Compte créé ! Remplissez votre annonce.', 'success');
            afficherZoneFormulaire(type);
            activerModeMatching();
            // Préremplir nom/prénom
            const pNom = document.getElementById(prefix === 'exp' ? 'exp-nom' : 'voy-nom');
            const pPrenom = document.getElementById(prefix === 'exp' ? 'exp-prenom' : 'voy-prenom');
            if (pNom) pNom.value = nom;
            if (pPrenom) pPrenom.value = prenom;
        } else {
            showAlert('❌ ' + (data.message || 'Erreur'), 'default');
        }
    })
    .catch(() => showAlert('❌ Erreur de connexion', 'default'));
}

function soumettreConnexion(type) {
    // type = 'expediteur' ou 'voyageur' selon la page
    const prefix = type === 'expediteur' ? 'exp' : 'voy';
    const username = document.getElementById(prefix + '-login-user')?.value.trim() || '';
    const password = document.getElementById(prefix + '-login-pass')?.value || '';

    if (!username || !password) {
        showAlert('⚠️ Identifiant et mot de passe requis', 'default');
        return;
    }

    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('type_profil', type); // ✅ séparation obligatoire

    fetch('/login-profil/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            window.EST_CONNECTE = true;
            localStorage.setItem('profil_connecte', JSON.stringify({
                nom_complet: data.nom_complet,
                type_profil: data.type_profil,
                profil_id: data.profil_id,
                guest_id: data.guest_id,
                telephone: data.telephone || ''
            }));
            showAlert('✅ Connexion réussie !', 'success');
            // ✅ Ne pas rediriger vers l'espace connecté : afficher directement
            // le formulaire Expédier/Voyager (pré-rempli si matching en cours),
            // exactement comme après une inscription.
            afficherZoneFormulaire(type);
            activerModeMatching();
        } else {
            showAlert('❌ ' + (data.message || 'Informations incorrectes'), 'default');
        }
    })
    .catch(function() {
        showAlert('❌ Erreur de connexion', 'default');
    });
}

// ================= MATCHING STORAGE =================
function selectionnerVoyageur(voyageurId) {
    localStorage.setItem('match_data', JSON.stringify({
        type: 'expediteur',
        voyageur_id: parseInt(voyageurId)
    }));
    // Plus de page Profil → page Expédier + auth
    showPage(null, 'expediteur');
    setTimeout(() => {
        if (typeof EST_CONNECTE !== 'undefined' && EST_CONNECTE) {
            afficherZoneFormulaire('expediteur');
            activerModeMatching();
        } else {
            afficherFormInscription('expediteur');
        }
    }, 200);
}

function selectionnerExpediteur(expediteurId) {
    localStorage.setItem('match_data', JSON.stringify({
        type: 'voyageur',
        expediteur_id: parseInt(expediteurId)
    }));
    localStorage.setItem('expediteur_a_preremplir', expediteurId);
    showPage(null, 'voyageur');
    setTimeout(() => {
        if (typeof EST_CONNECTE !== 'undefined' && EST_CONNECTE) {
            afficherZoneFormulaire('voyageur');
            activerModeMatching();
        } else {
            afficherFormInscription('voyageur');
        }
    }, 200);
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
            <a href="/accounts/google/login/"
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
            <button onclick="_fermerModalSansReset(); showPage(null, 'profil'); setTimeout(activerModeMatching, 300);"
                    style="width:100%;padding:13px;border-radius:12px;
                           background:linear-gradient(90deg,#0A1F44,#1E3A8A);color:white;
                           border:none;font-weight:700;font-size:0.95rem;cursor:pointer;
                           margin-bottom:10px;transition:all 0.2s;"
                    onmouseover="this.style.opacity='0.9'"
                    onmouseout="this.style.opacity='1'">
                ✍️ S'inscrire manuellement
            </button>
            <button onclick="_fermerModalSansReset(); showPage(null, 'login');"
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

// ✅ Fermeture SANS reset — utilisée quand l'utilisateur continue le process (S'inscrire / Se connecter)
function _fermerModalSansReset() {
    const modal = document.getElementById('modal-connexion-google');
    if (modal) modal.remove();
}

// ✅ Fermeture AVEC reset — utilisée quand l'utilisateur annule (bouton × ou clic dehors)
function fermerModalGoogle() {
    const modal = document.getElementById('modal-connexion-google');
    if (modal) modal.remove();

    // ✅ Réinitialiser tout — comme si l'utilisateur n'avait jamais cliqué sur Sélectionner

    // 1. Vider le localStorage de matching
    localStorage.removeItem('match_data');
    localStorage.removeItem('expediteur_a_preremplir');
    localStorage.removeItem('voyageur_prix_kg');

    // 2. Réinitialiser le formulaire expéditeur
    const formExp = document.getElementById('expediteur-form');
    if (formExp) formExp.reset();

    // Retirer les styles orange/jaune des champs préremplis
    ['exp-pays','exp-ville','exp-pays-dest','exp-ville-dest','exp-poids','exp-prix-kg'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.style.background = '';
            el.style.borderColor = '';
            el.removeAttribute('readonly');
            el.removeAttribute('max');
            el.placeholder = el.getAttribute('data-placeholder') || '';
        }
    });

    // Remettre le bouton expéditeur à son texte original
    const btnExp = document.getElementById('exp-submit');
    if (btnExp) {
        btnExp.textContent = 'Publier ma demande';
        btnExp.disabled = true;
    }

    // Réinitialiser le titre de la modal expéditeur
    const titleExp = document.querySelector('#expediteur-modal .modal-title');
    if (titleExp) titleExp.textContent = "Confirmer votre demande d'expédition";

    // Réinitialiser le total
    const totalEl = document.getElementById('exp-total');
    if (totalEl) totalEl.textContent = '0.00 €';

    // 3. Réinitialiser le formulaire voyageur
    const formVoy = document.getElementById('voyageur-form');
    if (formVoy) formVoy.reset();

    // Retirer les styles orange/jaune des champs préremplis voyageur
    ['voy-pays-depart','voy-ville-depart','voy-pays-destination','voy-ville-destination','voy-poids','voy-prix-kg'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.style.background = '';
            el.style.borderColor = '';
            el.removeAttribute('readonly');
        }
    });

    // Remettre le bouton voyageur à son texte original
    const btnVoy = document.getElementById('voy-submit');
    if (btnVoy) {
        btnVoy.textContent = 'Publier mon trajet';
        btnVoy.disabled = true;
    }

    // Réinitialiser le titre de la modal voyageur
    const titleVoy = document.querySelector('#voyageur-modal .modal-title');
    if (titleVoy) titleVoy.textContent = "Confirmer la publication de votre trajet";

    // Réinitialiser le gain
    const gainEl = document.getElementById('voy-gain');
    if (gainEl) gainEl.textContent = '0.00 €';

    // 4. Décocher les checkboxes
    ['exp-check1','exp-check2','voy-check1','voy-check2'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.checked = false;
    });

    // 5. Réinitialiser le moyen de paiement sélectionné
    const paymentHidden = document.getElementById('selected-payment');
    if (paymentHidden) paymentHidden.value = '';
    document.querySelectorAll('.payment-option').forEach(opt => opt.classList.remove('selected'));
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
            // ✅ Trajet — readonly
            const champsTrajet = {
                'exp-pays':      data.pays_depart,
                'exp-ville':     data.ville_depart,
                'exp-pays-dest': data.pays_destination,
                'exp-ville-dest':data.ville_destination,
            };
            Object.entries(champsTrajet).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el && val) {
                    el.value = val;
                    el.style.background = '#fffde7';
                    el.style.borderColor = '#FF7A00';
                    el.setAttribute('readonly', 'readonly');
                }
            });

            // ✅ Prix/kg — imposé par le voyageur, non modifiable
            const prixEl = document.getElementById('exp-prix-kg');
            if (prixEl && data.prix_par_kg) {
                prixEl.value = data.prix_par_kg;
                prixEl.style.background = '#fffde7';
                prixEl.style.border = '2px solid #FF7A00';
                prixEl.setAttribute('readonly', 'readonly');
            }

            // ✅ Poids — selon type_kg
            const poidsEl = document.getElementById('exp-poids');
            if (poidsEl) {
                if (data.type_kg === 'entier') {
                    // Entier → poids exact imposé, non modifiable
                    poidsEl.value = data.poids_disponible;
                    poidsEl.style.background = '#fffde7';
                    poidsEl.style.borderColor = '#FF7A00';
                    poidsEl.setAttribute('readonly', 'readonly');
                    showAlert(`✅ Trajet pré-rempli ! Poids fixe : ${data.poids_disponible} kg (tout ou rien).`, 'success');
                } else {
                    // Détail → expéditeur choisit mais ne peut pas dépasser le max
                    poidsEl.setAttribute('max', data.poids_disponible);
                    poidsEl.placeholder = `Max ${data.poids_disponible} kg disponibles`;
                    poidsEl.removeAttribute('readonly');
                    showAlert(`✅ Trajet pré-rempli ! Saisissez votre poids (max ${data.poids_disponible} kg).`, 'success');
                }
            }

            // ✅ Afficher le bouton Annuler
            const btnAnnuler = document.getElementById('exp-annuler-btn');
            if (btnAnnuler) btnAnnuler.style.display = 'block';

            calculerPrixExpediteur();
            verifierFormulaireExpediteur();
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
            // ✅ Trajet — readonly
            const champsTrajet = {
                'voy-pays-depart':      data.pays_depart,
                'voy-ville-depart':     data.ville_depart,
                'voy-pays-destination': data.pays_destination,
                'voy-ville-destination':data.ville_destination,
            };
            Object.entries(champsTrajet).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el && val) {
                    el.value = val;
                    el.style.background = '#fffde7';
                    el.style.borderColor = '#FF7A00';
                    el.setAttribute('readonly', 'readonly');
                }
            });

            // ✅ Poids — imposé par l'expéditeur, non modifiable
            const poidsEl = document.getElementById('voy-poids');
            if (poidsEl && data.poids) {
                poidsEl.value = data.poids;
                poidsEl.style.background = '#fffde7';
                poidsEl.style.borderColor = '#FF7A00';
                poidsEl.setAttribute('readonly', 'readonly');
            }

            // ✅ Prix/kg — imposé par l'expéditeur, non modifiable
            const prixEl = document.getElementById('voy-prix-kg');
            if (prixEl && data.prix_par_kg) {
                prixEl.value = data.prix_par_kg;
                prixEl.style.background = '#fffde7';
                prixEl.style.border = '2px solid #FF7A00';
                prixEl.setAttribute('readonly', 'readonly');
            }

            // ✅ Afficher le bouton Annuler
            const btnAnnuler = document.getElementById('voy-annuler-btn');
            if (btnAnnuler) btnAnnuler.style.display = 'block';

            calculerGainVoyageur();
            verifierFormulaireVoyageur();
            showAlert(`✅ Formulaire pré-rempli depuis l'annonce de l'expéditeur — Prix : ${data.prix_par_kg || 0}€/kg, Poids : ${data.poids} kg.`, 'success');
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
    const prixKg = parseFloat(document.getElementById('exp-prix-kg')?.value) || 0;
    const prixVoyageur = poids * prixKg;
    const montant = (prixVoyageur + 2.99).toFixed(2);   // total payé

    formData.append('nom', document.getElementById('exp-nom').value);
    formData.append('prenom', document.getElementById('exp-prenom').value);
    formData.append('telephone', getTelephoneComplet('exp-telephone'));
    formData.append('pays', document.getElementById('exp-pays').value);
    formData.append('ville', document.getElementById('exp-ville').value);
    formData.append('pays_destination', document.getElementById('exp-pays-dest').value);
    formData.append('ville_destination', document.getElementById('exp-ville-dest').value);
    formData.append('poids', poids);
    formData.append('prix_par_kg', prixKg);
    formData.append('prix', prixVoyageur);          // prix_total = ce que reçoit le voyageur
    formData.append('mode_paiement', document.getElementById('selected-payment').value);

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
            if (match.type === 'expediteur') localStorage.removeItem('match_data');

            document.getElementById('expediteur-form').reset();
            document.querySelectorAll('.payment-option').forEach(opt => opt.classList.remove('selected'));
            document.getElementById('selected-payment').value = '';
            document.getElementById('exp-total').textContent = '0.00 €';

            showAlert("💳 Redirection vers le paiement...", "success");
            setTimeout(() => {
                window.location.href = `/paiement/?expediteur_id=${data.expediteur_id}&mode_paiement=${document.getElementById('selected-payment')?.value || 'carte'}&montant=${montant}`;
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
    formData.append('nom', document.getElementById('voy-nom').value);
    formData.append('prenom', document.getElementById('voy-prenom').value);
    formData.append('telephone', getTelephoneComplet('voy-telephone'));
    formData.append('pays_depart', document.getElementById('voy-pays-depart').value);
    formData.append('ville_depart', document.getElementById('voy-ville-depart').value);
    formData.append('pays_destination', document.getElementById('voy-pays-destination').value);
    formData.append('ville_destination', document.getElementById('voy-ville-destination').value);
    formData.append('date_depart', document.getElementById('voy-date-depart').value);
    formData.append('heure_depart', document.getElementById('voy-heure-depart').value);
    formData.append('date_arrivee', document.getElementById('voy-date-arrivee').value);
    formData.append('heure_arrivee', document.getElementById('voy-heure-arrivee').value);
    formData.append('poids', document.getElementById('voy-poids').value);
    formData.append('prix_par_kg', document.getElementById('voy-prix-kg')?.value || 10);

    const typeKgEl = document.querySelector('input[name="type_kg"]:checked');
    formData.append('type_kg', typeKgEl ? typeKgEl.value : 'entier');

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
        // ✅ Pas connecté
        if (data.need_auth) {
            showAlert('⚠️ Connectez-vous pour publier', 'default');
            return;
        }

        if (data.status === 'ok') {
            closeModal('voyageur');
            localStorage.setItem('annonce_data', JSON.stringify({
                type: 'voyageur',
                id: data.voyageur_id
            }));
            localStorage.removeItem('match_data');
            localStorage.removeItem('expediteur_a_preremplir');

            const formVoy = document.getElementById('voyageur-form');
            if (formVoy) formVoy.reset();

            const gainEl = document.getElementById('voy-gain');
            if (gainEl) gainEl.textContent = '0.00 €';

            showAlert('✅ Trajet publié ! Redirection vers votre espace...', 'success');

            // ✅ Après publication → tableau de bord
            setTimeout(() => {
                window.location.href = data.redirect || '/espace-connecte/';
            }, 1000);
        } else {
            showAlert('❌ ' + (data.message || 'Erreur'), 'default');
        }
    })
    .catch(() => showAlert('❌ Erreur de connexion', 'default'));
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
            // ✅ Prix libre fixé par le voyageur
            const prixKg = data.prix_par_kg || 0;
            const prixVoyageur = poids * prixKg;
            const commission = 2.99; // commission fixe KERALINK
            const total = (prixVoyageur + commission).toFixed(2);

            // ✅ Stocker le prix_par_kg pour validerPaiementDirect
            localStorage.setItem('voyageur_prix_kg', prixKg);

            // Afficher modal de paiement direct
            afficherModalPaiementDirect(voyageurId, data, total, prixVoyageur, commission, profilData);
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
                    ${voyageurData.poids_disponible} kg × ${voyageurData.prix_par_kg || 0}€/kg + 2,99€ frais KERALINK
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

    // ✅ Prix par kg du voyageur (récupéré depuis data-prix-kg ou localStorage)
    const prixKgVoyageur = parseFloat(localStorage.getItem('voyageur_prix_kg') || '0') || 0;
    const prixVoyageur = poids * prixKgVoyageur;
    const montant = (prixVoyageur + 2.99).toFixed(2); // total = prix + commission 2.99€

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
    formData.append('prix_par_kg', prixKgVoyageur);
    formData.append('prix', prixVoyageur);
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
    // Cacher toutes les pages
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
 
    // ✅ Afficher la page cible
    const target = document.getElementById(pageId + '-page');
    if (target) {
        target.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
 
    // Mettre à jour les liens actifs dans la nav
    document.querySelectorAll('.nav-links a').forEach(link => link.classList.remove('active'));
    if (event && event.target) event.target.classList.add('active');
 
    // Déclencher le mode matching si nécessaire
    if (typeof activerModeMatching === 'function') {
        setTimeout(activerModeMatching, 150);
    }
 
    // ✅ Si l'utilisateur est connecté et vient de l'espace connecté,
    // pré-remplir son nom/email depuis le profil stocké
    if (sessionStorage.getItem('from_espace') === '1') {
        sessionStorage.removeItem('from_espace');
        const profil = JSON.parse(localStorage.getItem('profil_connecte') || '{}');
        if (profil && profil.nom_complet) {
            const parts = profil.nom_complet.split(' ');
            const prenom = parts[0] || '';
            const nom = parts.slice(1).join(' ') || '';
 
            if (pageId === 'expediteur') {
                const nomEl = document.getElementById('exp-nom');
                const prenomEl = document.getElementById('exp-prenom');
                const telEl = document.getElementById('exp-telephone');
                if (nomEl && !nomEl.value) nomEl.value = nom;
                if (prenomEl && !prenomEl.value) prenomEl.value = prenom;
                if (telEl && !telEl.value && profil.telephone) telEl.value = profil.telephone;
            } else if (pageId === 'voyageur') {
                const nomEl = document.getElementById('voy-nom');
                const prenomEl = document.getElementById('voy-prenom');
                const telEl = document.getElementById('voy-telephone');
                if (nomEl && !nomEl.value) nomEl.value = nom;
                if (prenomEl && !prenomEl.value) prenomEl.value = prenom;
                if (telEl && !telEl.value && profil.telephone) telEl.value = profil.telephone;
            }
        }
    }
}

function showLoginForm() { showPage(null, 'login'); }

// ================= INITIALISATION =================
document.addEventListener('DOMContentLoaded', function () {
    // ✅ CORRECTIF — Ouvrir directement Expédier / Voyager quand on revient
    // de l'espace connecté (?open=expediteur|voyageur), au lieu de forcer
    // systématiquement la page d'accueil. Gère aussi le sessionStorage en secours.
    const paramsInit = new URLSearchParams(window.location.search);
    const openFormInit = paramsInit.get('open') || sessionStorage.getItem('open_form');

    if (openFormInit === 'expediteur' || openFormInit === 'voyageur') {
        sessionStorage.removeItem('open_form');
        sessionStorage.removeItem('from_espace');
        if (window.history.replaceState) {
            window.history.replaceState({}, '', window.location.pathname);
        }
        showPage(null, openFormInit);
        // Utilisateur déjà connecté → on saute l'auth et on va direct au formulaire
        if (typeof EST_CONNECTE !== 'undefined' && EST_CONNECTE) {
            if (typeof afficherZoneFormulaire === 'function') afficherZoneFormulaire(openFormInit);
        } else if (typeof afficherFormInscription === 'function') {
            afficherFormInscription(openFormInit);
        }
    } else {
        showPage(null, 'home');
    }

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

// ================= CALCUL PRIX EXPÉDITEUR =================
// Affiche UNIQUEMENT le montant voyageur (sans les 2.99€)
function calculerPrixExpediteur() {
    const poids = parseFloat(document.getElementById('exp-poids')?.value) || 0;
    const prixKg = parseFloat(document.getElementById('exp-prix-kg')?.value) || 0;

    const prixVoyageur = poids * prixKg;

    const elTotal = document.getElementById('exp-total');
    if (elTotal) {
        elTotal.textContent = prixVoyageur.toFixed(2) + ' €';
    }
}

// ================= CALCUL GAIN VOYAGEUR =================
function calculerGainVoyageur() {
    const poids = parseFloat(document.getElementById('voy-poids')?.value) || 0;
    const prixKg = parseFloat(document.getElementById('voy-prix-kg')?.value) || 0;

    const gain = poids * prixKg;

    const elGain = document.getElementById('voy-gain');
    if (elGain) {
        elGain.textContent = gain.toFixed(2) + ' €';
    }
}

function selectPayment(element, method) {
    document.querySelectorAll('.payment-option').forEach(opt => opt.classList.remove('selected'));
    element.classList.add('selected');
    document.getElementById('selected-payment').value = method;
    verifierFormulaireExpediteur();
}

function verifierFormulaireExpediteur() {
    const required = ['exp-nom','exp-prenom','exp-telephone','exp-pays','exp-ville',
                      'exp-pays-dest','exp-ville-dest','exp-poids','exp-prix-kg'];
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
                      'voy-heure-depart','voy-date-arrivee','voy-heure-arrivee','voy-poids','voy-prix-kg'];
    const valid = required.every(id => document.getElementById(id)?.value?.trim());
    const check1 = document.getElementById('voy-check1')?.checked;
    const check2 = document.getElementById('voy-check2')?.checked;
    const btn = document.getElementById('voy-submit');

    // ✅ Contrôle de chronologie : l'arrivée doit être après le départ
    const chronoOk = verifierChronologieVoyageur();

    if (btn) btn.disabled = !(valid && check1 && check2 && chronoOk);
    calculerGainVoyageur();
}

// ✅ Vérifie que la date/heure d'arrivée est bien postérieure à la date/heure de départ
function verifierChronologieVoyageur() {
    const dateDepart   = document.getElementById('voy-date-depart')?.value;
    const heureDepart  = document.getElementById('voy-heure-depart')?.value;
    const dateArrivee  = document.getElementById('voy-date-arrivee')?.value;
    const heureArrivee = document.getElementById('voy-heure-arrivee')?.value;

    const zoneErreur = document.getElementById('voy-erreur-chrono');

    // Tant que les 4 champs ne sont pas remplis, on ne bloque pas encore (message masqué)
    if (!dateDepart || !heureDepart || !dateArrivee || !heureArrivee) {
        if (zoneErreur) zoneErreur.style.display = 'none';
        return true;
    }

    const depart  = new Date(`${dateDepart}T${heureDepart}`);
    const arrivee = new Date(`${dateArrivee}T${heureArrivee}`);

    if (arrivee <= depart) {
        if (zoneErreur) {
            zoneErreur.textContent = "❌ La date/heure d'arrivée doit être postérieure à la date/heure de départ.";
            zoneErreur.style.display = 'block';
        }
        return false;
    }

    if (zoneErreur) zoneErreur.style.display = 'none';
    return true;
}

function ouvrirModalExpediteur() {
    const nom = document.getElementById('exp-nom').value;
    const prenom = document.getElementById('exp-prenom').value;
    const poids = parseFloat(document.getElementById('exp-poids').value) || 0;
    // ✅ Prix libre saisi par l'expéditeur
    const prixKg = parseFloat(document.getElementById('exp-prix-kg')?.value) || 0;
    const prixVoyageur = poids * prixKg;
    const commission = 2.99;
    const total = prixVoyageur + commission;

    document.getElementById('exp-confirmation-details').innerHTML = `
        <p><strong>Nom :</strong> ${nom} ${prenom}</p>
        <p><strong>Trajet :</strong> ${document.getElementById('exp-ville').value} → ${document.getElementById('exp-ville-dest').value}</p>
        <p><strong>Poids :</strong> ${poids} kg</p>
        <p><strong>Prix/kg :</strong> ${prixKg.toFixed(2)} €/kg</p>
        <p><strong>Montant voyageur :</strong> ${prixVoyageur.toFixed(2)} €</p>
        <p><strong>Frais KERALINK :</strong> ${commission.toFixed(2)} €</p>
        <p><strong>Total à payer :</strong> <strong style="color:#FF7A00">${total.toFixed(2)} €</strong></p>
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

    // ✅ Prix libre saisi par le voyageur
    const prixKg = parseFloat(document.getElementById('voy-prix-kg')?.value) || 0;
    const gainEstime = (poids * prixKg).toFixed(2);

    document.getElementById('voy-confirmation-details').innerHTML = `
        <p><strong>Nom :</strong> ${nom} ${prenom}</p>
        <p><strong>Trajet :</strong> ${document.getElementById('voy-ville-depart').value} → ${document.getElementById('voy-ville-destination').value}</p>
        <p><strong>Poids disponible :</strong> ${poids} kg</p>
        <p><strong>Votre prix :</strong> ${prixKg.toFixed(2)} €/kg</p>
        <p><strong>Gain estimé (si complet) :</strong> <strong style="color:#2e7d32">${gainEstime} €</strong></p>
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
// REMPLACEZ la fonction setLangue dans votre script.js
// Cette version utilise Django i18n côté serveur + rechargement
// ================================================================

function setLangue(code) {
    const flags = { fr: '🇫🇷', en: '🇬🇧' };
    const labels = { fr: 'FR', en: 'EN' };

    // Mettre à jour le bouton dans le header
    const flagEl  = document.getElementById('lang-flag');
    const labelEl = document.getElementById('lang-label');
    if (flagEl)  flagEl.textContent  = flags[code]  || '🇫🇷';
    if (labelEl) labelEl.textContent = labels[code] || 'FR';

    // Fermer le menu
    const menu = document.getElementById('lang-menu');
    if (menu) menu.style.display = 'none';

    // ✅ Envoyer la langue au serveur Django puis recharger la page
    const formData = new FormData();
    formData.append('langue', code);

    fetch('/changer-langue/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            // ✅ Recharger la page pour appliquer les traductions Django
            location.reload();
        }
    })
    .catch(() => {});
}

// ℹ️ L'ancien système de traduction par dictionnaire JS (TRADUCTIONS /
// langueActuelle / _appliquerTraductions / data-i18n) a été retiré : ces
// variables n'étaient jamais déclarées (d'où les erreurs "is not defined"
// au chargement) et faisaient doublon avec les traductions Django ({% trans %})
// déjà rendues côté serveur. La langue et les textes sont désormais gérés
// entièrement par Django (gettext + {% trans %}), pas par du JS.

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

// Commission fixe KERALINK
const COMMISSION_KERALINK = 2.99;

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

    // ✅ Mettre à jour le total du formulaire expéditeur si rempli (prix libre)
    const poidsExpEl = document.getElementById('exp-poids');
    const prixKgExpEl = document.getElementById('exp-prix-kg');
    if (poidsExpEl && poidsExpEl.value && prixKgExpEl && prixKgExpEl.value) {
        calculerPrixExpediteur();
    }

    // ✅ Mettre à jour le gain du formulaire voyageur si rempli (prix libre)
    const poidsVoyEl = document.getElementById('voy-poids');
    if (poidsVoyEl && poidsVoyEl.value) {
        calculerGainVoyageur();
    }
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

// ✅ Initialisation au chargement
document.addEventListener('DOMContentLoaded', function () {
    // ℹ️ Le bouton de langue est désormais affiché correctement dès le
    // rendu serveur (Django i18n) — plus besoin de le resynchroniser en JS.
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
 * ✅ Reconstitue le numéro complet (indicatif + numéro saisi) pour un champ
 * téléphone équipé du sélecteur d'indicatif (creerIndicatifTel). L'input ne
 * contient que les chiffres locaux : l'indicatif est stocké séparément sur
 * le bouton .indicatif-btn juste à côté (attribut data-code).
 */
function getTelephoneComplet(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return '';
    const numero = input.value.trim();
    if (!numero) return '';
    if (numero.startsWith('+')) return numero; // déjà complet, ne rien dupliquer
    const wrap = input.closest('.indicatif-wrap');
    const btn = wrap ? wrap.querySelector('.indicatif-btn') : null;
    const code = btn ? btn.getAttribute('data-code') : '';
    return (code || '') + numero.replace(/^0+/, ''); // retire le 0 initial local si présent
}

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
                        📋 Grille tarifaire KERALINK
                    </div>
                    <table style="width:100%;border-collapse:collapse;">
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:14px 20px;font-size:0.92rem;">💼 Prix par kg</td>
                            <td style="padding:14px 20px;text-align:right;font-weight:bold;color:#2e7d32;font-size:1.05rem;">
                                Libre
                            </td>
                        </tr>
                        <tr style="border-bottom:1px solid #eee;background:#fafafa;">
                            <td style="padding:14px 20px;font-size:0.92rem;">🏢 Commission KERALINK</td>
                            <td style="padding:14px 20px;text-align:right;font-weight:bold;color:#FF7A00;font-size:1.1rem;">
                                2,99 € fixe
                            </td>
                        </tr>
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:14px 20px;font-size:0.92rem;">💸 Total payé par l'expéditeur</td>
                            <td style="padding:14px 20px;text-align:right;font-weight:bold;color:#0A1F44;">
                                (Poids × Prix/kg) + 2,99 €
                            </td>
                        </tr>
                        <tr style="background:#fff3e0;">
                            <td style="padding:14px 20px;font-size:0.92rem;">↩️ Remboursement (si annulation)</td>
                            <td style="padding:14px 20px;text-align:right;font-weight:bold;color:#e65100;">
                                Prix versé au voyageur (sans les 2,99 €)
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- Exemples -->
                <h3 style="color:#0A1F44;margin-bottom:14px;">📦 Exemples concrets</h3>
                <div style="display:grid;gap:12px;margin-bottom:20px;">
                    ${[
                        { kg: 5,  prix: 8,  label: 'Petit colis (5 kg à 8 €/kg)' },
                        { kg: 10, prix: 6,  label: 'Colis moyen (10 kg à 6 €/kg)' },
                        { kg: 23, prix: 5,  label: 'Grande valise (23 kg à 5 €/kg)' },
                    ].map(ex => `
                        <div style="background:#f5f5f5;border-radius:10px;padding:14px 18px;
                                    display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <strong>${ex.label}</strong>
                                <div style="font-size:0.82rem;color:#888;margin-top:2px;">
                                    Voyageur reçoit : <strong style="color:#2e7d32;">${(ex.kg * ex.prix).toFixed(2)} €</strong>
                                    &nbsp;|&nbsp; Commission KERALINK : <strong>2,99 €</strong>
                                </div>
                            </div>
                            <div style="font-size:1.15rem;font-weight:bold;color:#FF7A00;">
                                ${((ex.kg * ex.prix) + 2.99).toFixed(2)} €
                            </div>
                        </div>
                    `).join('')}
                </div>

                <div style="background:#e8f5e9;border-radius:10px;padding:14px;border-left:4px solid #2e7d32;font-size:0.88rem;color:#555;">
                    ✅ <strong>Aucun frais caché.</strong><br>
                    • Le voyageur et l’expéditeur fixent librement le prix au kg.<br>
                    • KERALINK prélève uniquement une commission fixe de <strong>2,99 €</strong> par transaction.<br>
                    • En cas de remboursement, l’expéditeur récupère le montant versé au voyageur (les 2,99 € restent non remboursables).
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

// ================================================================
// ✅ ANNULER LE FORMULAIRE — réinitialise tout + retour accueil
// ================================================================
function annulerFormulaire(type) {
    // Nettoyer localStorage et sessionStorage
    localStorage.removeItem('match_data');
    localStorage.removeItem('expediteur_a_preremplir');
    localStorage.removeItem('voyageur_prix_kg');
    sessionStorage.removeItem('open_form');
    sessionStorage.removeItem('from_espace');

    if (type === 'expediteur') {
        const form = document.getElementById('expediteur-form');
        if (form) form.reset();

        // Retirer readonly et styles sur tous les champs
        ['exp-nom','exp-prenom','exp-telephone','exp-pays','exp-ville',
         'exp-pays-dest','exp-ville-dest','exp-poids','exp-prix-kg'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.removeAttribute('readonly');
                el.removeAttribute('max');
                el.style.background = '';
                el.style.borderColor = '';
                el.style.borderWidth = '';
            }
        });
        // Remettre la bordure orange sur prix-kg
        const prixEl = document.getElementById('exp-prix-kg');
        if (prixEl) prixEl.style.border = '2px solid #FF7A00';

        // Remettre le texte du bouton submit
        const btnSubmit = document.getElementById('exp-submit');
        if (btnSubmit) btnSubmit.textContent = 'Publier ma demande';

        // Cacher le bouton Annuler
        const btnAnnuler = document.getElementById('exp-annuler-btn');
        if (btnAnnuler) btnAnnuler.style.display = 'none';

        // Décocher les cases
        ['exp-check1','exp-check2'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.checked = false;
        });

        // Réinitialiser le total
        const totalEl = document.getElementById('exp-total');
        if (totalEl) totalEl.textContent = '0.00 €';

        // Réinitialiser paiement
        const payHidden = document.getElementById('selected-payment');
        if (payHidden) payHidden.value = '';
        document.querySelectorAll('.payment-option').forEach(o => o.classList.remove('selected'));

    } else if (type === 'voyageur') {
        const form = document.getElementById('voyageur-form');
        if (form) form.reset();

        // Retirer readonly et styles
        ['voy-nom','voy-prenom','voy-telephone','voy-pays-depart','voy-ville-depart',
         'voy-pays-destination','voy-ville-destination','voy-poids','voy-prix-kg'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.removeAttribute('readonly');
                el.removeAttribute('max');
                el.style.background = '';
                el.style.borderColor = '';
                el.style.borderWidth = '';
            }
        });
        // Remettre la bordure verte sur prix-kg voyageur
        const prixVoyEl = document.getElementById('voy-prix-kg');
        if (prixVoyEl) prixVoyEl.style.border = '2px solid #2e7d32';

        // Remettre le texte du bouton submit
        const btnSubmit = document.getElementById('voy-submit');
        if (btnSubmit) btnSubmit.textContent = 'Publier mon trajet';

        // Cacher le bouton Annuler
        const btnAnnuler = document.getElementById('voy-annuler-btn');
        if (btnAnnuler) btnAnnuler.style.display = 'none';

        // Décocher les cases
        ['voy-check1','voy-check2'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.checked = false;
        });

        // Réinitialiser le gain
        const gainEl = document.getElementById('voy-gain');
        if (gainEl) gainEl.textContent = '0.00 €';

        // Remettre type_kg à entier
        const radioEntier = document.querySelector('input[name="type_kg"][value="entier"]');
        if (radioEntier) radioEntier.checked = true;
    }

    // ✅ Réinitialiser les IDs de matching
    if (typeof window !== 'undefined') {
        window.voyageurSelectId = null;
        window.expediteurSelectId = null;
    }

    // ✅ Déconnecter l'utilisateur : au prochain clic sur "Expédier" ou
    // "Voyager" il devra repasser par l'inscription/connexion (auth).
    localStorage.removeItem('profil_connecte');
    if (typeof window !== 'undefined') window.EST_CONNECTE = false;
    window.location.href = '/deconnexion/';
}

// ================================================================
// ✅ VALIDATION POIDS EXPÉDITEUR (max = poids voyageur)
// ================================================================
function validerPoidsExpediteur() {
    const poidsEl = document.getElementById('exp-poids');
    if (!poidsEl) return;
    const maxVal = parseFloat(poidsEl.getAttribute('max') || '0');
    if (!maxVal) return; // Pas de max défini = pas de matching = libre
    const valActuelle = parseFloat(poidsEl.value) || 0;
    if (valActuelle > maxVal) {
        // ✅ Remettre la valeur max et afficher un message
        poidsEl.value = maxVal;
        showAlert('⚠️ Veuillez respecter le nombre de kg maximum (' + maxVal + ' kg).', 'default');
    }
}

// ================================================================
// ✅ PUBLIER DEPUIS ESPACE CONNECTÉ
// ================================================================
function publierDepuisEspace() {
    const profil = JSON.parse(localStorage.getItem('profil_connecte') || '{}');
    const type = profil.type_profil || '';
    if (!type) return;
    sessionStorage.setItem('open_form', type);
    sessionStorage.setItem('from_espace', '1');
    window.location.href = '/?open=' + encodeURIComponent(type);
}
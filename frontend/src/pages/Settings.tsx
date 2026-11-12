import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { changePassword, getCurrentUser, updateUsername, type CurrentUser } from "../api/auth";
import Header from "../components/Header";

function describe(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

export default function Settings() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loadError, setLoadError] = useState("");
  const [username, setUsername] = useState("");
  const [profileStatus, setProfileStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordStatus, setPasswordStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const [savingPassword, setSavingPassword] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then((current) => {
        setUser(current);
        setUsername(current.username);
      })
      .catch((reason: unknown) => setLoadError(describe(reason, "Unable to load your account.")));
  }, []);

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    setSavingProfile(true);
    setProfileStatus(null);
    try {
      const updated = await updateUsername(username.trim());
      setUser(updated);
      setUsername(updated.username);
      setProfileStatus({ ok: true, text: "Username updated." });
    } catch (reason) {
      setProfileStatus({ ok: false, text: describe(reason, "Unable to update the username.") });
    } finally {
      setSavingProfile(false);
    }
  }

  async function savePassword(event: FormEvent) {
    event.preventDefault();
    setPasswordStatus(null);
    if (newPassword !== confirmPassword) {
      setPasswordStatus({ ok: false, text: "The new passwords do not match." });
      return;
    }
    setSavingPassword(true);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordStatus({ ok: true, text: "Password changed." });
    } catch (reason) {
      setPasswordStatus({ ok: false, text: describe(reason, "Unable to change the password.") });
    } finally {
      setSavingPassword(false);
    }
  }

  return (
    <div className="app">
      <Header />
      <main className="settings-page">
        <div className="settings-heading">
          <h1>Account settings</h1>
          <Link to="/chat">Back to chat</Link>
        </div>
        {loadError && <p className="auth-error" role="alert">{loadError}</p>}

        <section className="settings-card" aria-labelledby="profile-heading">
          <h2 id="profile-heading">Profile</h2>
          <form className="auth-form" onSubmit={saveProfile}>
            <div className="auth-field">
              <label htmlFor="settings-email">Email</label>
              <input id="settings-email" type="email" value={user?.email ?? ""} readOnly disabled />
            </div>
            <div className="auth-field">
              <label htmlFor="settings-username">Username</label>
              <input id="settings-username" type="text" autoComplete="username" minLength={3} maxLength={50}
                value={username} onChange={(event) => setUsername(event.target.value)} required disabled={!user} />
            </div>
            {profileStatus && <p className={profileStatus.ok ? "settings-success" : "auth-error"} role={profileStatus.ok ? "status" : "alert"}>{profileStatus.text}</p>}
            <button className="auth-submit" type="submit"
              disabled={!user || savingProfile || username.trim() === user.username || username.trim().length < 3}>
              {savingProfile ? "Saving…" : "Save username"}
            </button>
          </form>
        </section>

        <section className="settings-card" aria-labelledby="password-heading">
          <h2 id="password-heading">Password</h2>
          <form className="auth-form" onSubmit={savePassword}>
            <div className="auth-field">
              <label htmlFor="settings-current">Current password</label>
              <input id="settings-current" type="password" autoComplete="current-password"
                value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required />
            </div>
            <div className="auth-field">
              <label htmlFor="settings-new">New password</label>
              <input id="settings-new" type="password" autoComplete="new-password" minLength={8} maxLength={128}
                value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required />
            </div>
            <div className="auth-field">
              <label htmlFor="settings-confirm">Confirm new password</label>
              <input id="settings-confirm" type="password" autoComplete="new-password" minLength={8} maxLength={128}
                value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
            </div>
            {passwordStatus && <p className={passwordStatus.ok ? "settings-success" : "auth-error"} role={passwordStatus.ok ? "status" : "alert"}>{passwordStatus.text}</p>}
            <button className="auth-submit" type="submit" disabled={savingPassword}>
              {savingPassword ? "Changing…" : "Change password"}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

import { useState } from "react";
import api from "./api";
import "./Login.css";

function Login({ onLogin }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (loading) return;

        setError("");
        setLoading(true);

        try {
            const formData = new URLSearchParams();
            formData.append("username", username);
            formData.append("password", password);

            const response = await api.post("/auth/token", formData, {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            });

            localStorage.setItem("token", response.data.access_token);
            onLogin();
        } catch (error) {
            setError(
                error.response?.status === 400 ||
                    error.response?.status === 401
                    ? "Invalid username or password."
                    : "Unable to sign in. Please try again."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="login-page">
            <div className="login-card">
                <div className="login-brand">
                    <div className="login-logo">+</div>
                    <h1>MedFlow</h1>
                    <p>Healthcare Equipment Management System</p>
                </div>

                <div className="login-heading">
                    <h2>Welcome back</h2>
                    <p>Sign in to access your dashboard</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="login-field">
                        <label htmlFor="login-username">Username</label>
                        <input
                            id="login-username"
                            type="text"
                            placeholder="Enter your username"
                            autoComplete="username"
                            value={username}
                            onChange={(event) => setUsername(event.target.value)}
                            required
                        />
                    </div>

                    <div className="login-field">
                        <label htmlFor="login-password">Password</label>

                        <div className="login-password-wrapper">
                            <input
                                id="login-password"
                                type={showPassword ? "text" : "password"}
                                placeholder="Enter your password"
                                autoComplete="current-password"
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                required
                            />

                            <button
                                type="button"
                                className="login-password-toggle"
                                onClick={() => setShowPassword(!showPassword)}
                                aria-label={
                                    showPassword ? "Hide password" : "Show password"
                                }
                            >
                                {showPassword ? "Hide" : "Show"}
                            </button>
                        </div>
                    </div>

                    {error && (
                        <p className="login-error" role="alert">
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        className="login-submit"
                        disabled={loading}
                    >
                        {loading ? "Signing in..." : "Sign In →"}
                    </button>
                </form>

                <p className="login-security">
                    Authorized personnel only
                </p>
            </div>

            <p className="login-footer">
                © 2026 MedFlow · Clinical Operations Platform
            </p>
        </main>
    );
}

export default Login;
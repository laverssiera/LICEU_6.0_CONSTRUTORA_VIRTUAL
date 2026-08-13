import { useEffect, useState } from 'react';

export function useCurrentUser() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Exemplo: buscar usuário do localStorage ou endpoint
    const raw = window.localStorage.getItem('liceu_user');
    if (raw) {
      try {
        setUser(JSON.parse(raw));
      } catch {
        setUser(null);
      }
    } else {
      setUser(null);
    }
  }, []);

  return user;
}

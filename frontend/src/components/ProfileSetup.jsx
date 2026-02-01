import { useState } from 'react';
import { User, Server, Globe, Key, Plus, Trash2, Save } from 'lucide-react';
import { useUser } from '@clerk/clerk-react';
import { useNavigate } from 'react-router-dom';

const ProfileSetup = () => {
  const { user } = useUser();
  const navigate = useNavigate();

  // Global User Info
  const [userName, setUserName] = useState(user?.fullName || '');

  // Server List State
  const [servers, setServers] = useState([
    {
      id: Date.now(),
      serverTag: '',
      ipAddress: '',
      hostname: '',
      sshUsername: 'ubuntu',
      // Security
      selectedFileType: 'pem', // 'pem' or 'ppk'
      pemFile: null,
      ppkFile: null,
      serverPassword: '',
    }
  ]);

  const handleUserChange = (e) => {
    setUserName(e.target.value);
  };

  const handleServerChange = (id, e) => {
    const { name, value, files } = e.target;
    setServers(prevServers => prevServers.map(server => {
      if (server.id === id) {
        if (files) {
          return { ...server, [name]: files[0] };
        }
        return { ...server, [name]: value };
      }
      return server;
    }));
  };

  const handleFileTypeChange = (id, type) => {
    setServers(prevServers => prevServers.map(server => {
      if (server.id === id) {
        return {
          ...server,
          selectedFileType: type,
          pemFile: null,
          ppkFile: null
        };
      }
      return server;
    }));
  };

  const addServer = () => {
    const newServer = {
      id: Date.now(),
      serverTag: '',
      ipAddress: '',
      hostname: '',
      sshUsername: 'ubuntu',
      selectedFileType: 'pem',
      pemFile: null,
      ppkFile: null,
      serverPassword: '',
    };
    setServers([...servers, newServer]);
  };

  const removeServer = (id) => {
    if (servers.length > 1) {
      setServers(servers.filter(server => server.id !== id));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Basic IP Validation
    const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
    for (const server of servers) {
      if (!ipRegex.test(server.ipAddress)) {
        alert(`Invalid IP Address for server: ${server.serverTag}`);
        return;
      }
    }

    // Process servers to read file content
    const processingServers = servers.map(async (server) => {
      let sshKeyContent = null;
      const file = server.selectedFileType === 'pem' ? server.pemFile : server.ppkFile;

      if (file) {
        sshKeyContent = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (event) => resolve(event.target.result);
          reader.onerror = (error) => reject(error);
          reader.readAsText(file);
        });
      }

      return {
        ...server,
        sshKeyContent
      };
    });

    try {
      const serversWithKeys = await Promise.all(processingServers);

      const finalData = {
        userId: user?.id,
        email: user?.primaryEmailAddress?.emailAddress,
        userName,
        servers: serversWithKeys
      };
      console.log('Profile Data:', finalData);

      const response = await fetch('http://localhost:8000/api/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(finalData),
      });

      if (response.ok) {
        navigate('/dashboard');
      } else {
        console.error('Failed to save profile');
        alert('Failed to save profile. Please try again.');
        const err = await response.json();
        console.error(err);
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      alert('An error occurred. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-base-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="w-20 h-20 bg-primary/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <User className="w-10 h-10 text-primary" />
          </div>
          <h1 className="text-4xl font-bold text-base-content mb-4">
            Complete Your Profile Setup
          </h1>
          <p className="text-xl text-base-content/70 max-w-2xl mx-auto">
            Configure your server details and add multiple servers for your orchestration setup
          </p>
        </div>

        {/* Main Form */}
        <div className="bg-base-100 rounded-2xl shadow-xl border border-base-300 p-8">
          <form onSubmit={handleSubmit}>

            {/* User Information (Global) */}
            <div className="space-y-6 mb-12">
              <h2 className="text-2xl font-bold text-base-content mb-6 flex items-center gap-2">
                <User className="w-6 h-6" />
                User Information
              </h2>

              <div className="form-control">
                <label className="label">
                  <span className="label-text text-base-content font-medium">Full Name</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={userName}
                  onChange={handleUserChange}
                  className="input input-bordered w-full bg-base-200 border-base-300 focus:border-primary"
                  placeholder="Enter your full name"
                  required
                />
              </div>
            </div>

            {/* Servers List */}
            <div className="space-y-12">
              {servers.map((server, index) => (
                <div key={server.id} className="p-6 border border-base-300 rounded-xl bg-base-50/50 relative">

                  <div className="flex justify-between items-start mb-6">
                    <h2 className="text-2xl font-bold text-base-content flex items-center gap-2">
                      <Server className="w-6 h-6" />
                      Server #{index + 1} Configuration
                    </h2>
                    {servers.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeServer(server.id)}
                        className="btn btn-error btn-sm gap-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        Remove
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Server Details */}
                    <div className="space-y-6">
                      <div className="form-control">
                        <label className="label">
                          <span className="label-text text-base-content font-medium">Server Tag</span>
                          <span className="label-text-alt text-base-content/60">Used for identification</span>
                        </label>
                        <input
                          type="text"
                          name="serverTag"
                          value={server.serverTag}
                          onChange={(e) => handleServerChange(server.id, e)}
                          className="input input-bordered w-full bg-base-200 border-base-300 focus:border-primary"
                          placeholder="e.g., Production-Server-01"
                          required
                        />
                      </div>

                      <div className="form-control">
                        <label className="label">
                          <span className="label-text text-base-content font-medium">IP Address</span>
                        </label>
                        <input
                          type="text"
                          name="ipAddress"
                          value={server.ipAddress}
                          onChange={(e) => handleServerChange(server.id, e)}
                          className="input input-bordered w-full bg-base-200 border-base-300 focus:border-primary"
                          placeholder="e.g., 192.168.1.100"
                          required
                        />
                      </div>

                      <div className="form-control">
                        <label className="label">
                          <span className="label-text text-base-content font-medium">Hostname</span>
                        </label>
                        <input
                          type="text"
                          name="hostname"
                          value={server.hostname}
                          onChange={(e) => handleServerChange(server.id, e)}
                          className="input input-bordered w-full bg-base-200 border-base-300 focus:border-primary"
                          placeholder="e.g., server01.example.com"
                          required
                        />
                      </div>

                      <div className="form-control">
                        <label className="label">
                          <span className="label-text text-base-content font-medium">SSH Username</span>
                        </label>
                        <input
                          type="text"
                          name="sshUsername"
                          value={server.sshUsername}
                          onChange={(e) => handleServerChange(server.id, e)}
                          className="input input-bordered w-full bg-base-200 border-base-300 focus:border-primary"
                          placeholder="e.g., ubuntu, root, ec2-user"
                          required
                        />
                      </div>
                    </div>

                    {/* Security Config (Per Server) */}
                    <div className="space-y-6">
                      <h3 className="text-xl font-semibold text-base-content mb-4 flex items-center gap-2">
                        <Key className="w-5 h-5 text-base-content/70" />
                        Security
                      </h3>

                      {/* Key File Type Selection */}
                      <div className="flex gap-2 mb-2">
                        <button
                          type="button"
                          onClick={() => handleFileTypeChange(server.id, 'pem')}
                          className={`btn btn-sm ${server.selectedFileType === 'pem' ? 'btn-primary' : 'btn-ghost'}`}
                        >
                          PEM
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFileTypeChange(server.id, 'ppk')}
                          className={`btn btn-sm ${server.selectedFileType === 'ppk' ? 'btn-primary' : 'btn-ghost'}`}
                        >
                          PPK
                        </button>
                      </div>

                      <div className="form-control">
                        <label className="label">
                          <span className="label-text text-base-content font-medium">
                            {server.selectedFileType === 'pem' ? 'PEM Key File' : 'PPK Key File'}
                          </span>
                        </label>
                        <input
                          type="file"
                          name={server.selectedFileType === 'pem' ? 'pemFile' : 'ppkFile'}
                          onChange={(e) => handleServerChange(server.id, e)}
                          className="file-input file-input-bordered w-full bg-base-200 border-base-300 file-input-sm"
                          accept={server.selectedFileType === 'pem' ? '.pem' : '.ppk'}
                        />
                        {server[server.selectedFileType === 'pem' ? 'pemFile' : 'ppkFile'] && (
                          <p className="mt-2 text-xs text-success">
                            ✓ {server[server.selectedFileType === 'pem' ? 'pemFile' : 'ppkFile'].name}
                          </p>
                        )}
                      </div>

                      <div className="form-control">
                        <label className="label">
                          <span className="label-text text-base-content font-medium">Server Password</span>
                        </label>
                        <input
                          type="password"
                          name="serverPassword"
                          value={server.serverPassword}
                          onChange={(e) => handleServerChange(server.id, e)}
                          className="input input-bordered w-full bg-base-200 border-base-300 focus:border-primary"
                          placeholder="Optional if using key"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Add Server Button */}
            <div className="mt-8 flex justify-center">
              <button
                type="button"
                onClick={addServer}
                className="btn btn-outline btn-primary gap-2"
              >
                <Plus className="w-5 h-5" />
                Add Another Server
              </button>
            </div>

            {/* Submit Button */}
            <div className="mt-12 pt-8 border-t border-base-300">
              <div className="flex justify-center">
                <button
                  type="submit"
                  className="btn btn-primary btn-lg gap-3 px-8"
                >
                  <Save className="w-5 h-5" />
                  Save Profile & Continue
                </button>
              </div>
              <p className="text-center text-base-content/60 mt-4">
                You can always update these settings later from your profile
              </p>
            </div>
          </form>
        </div>

        {/* Progress Indicator */}
        <div className="mt-8 flex justify-center">
          <div className="steps">
            <div className="step step-primary">Login</div>
            <div className="step step-primary">Profile Setup</div>
            <div className="step">Dashboard</div>
          </div>
        </div>
      </div >
    </div >
  );
};

export default ProfileSetup;
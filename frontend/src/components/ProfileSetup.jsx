import { useState } from 'react';
import { User, Server, Globe, Key, Plus, Trash2, Save } from 'lucide-react';
import { useUser } from '@clerk/clerk-react';

const ProfileSetup = () => {
  const { user } = useUser();
  const [formData, setFormData] = useState({
    name: user?.fullName || '',
    serverTag: '',
    ipAddress: '',
    hostname: '',
    pemFile: null,
    ppkFile: null,
    serverPassword: '',
  });

  const [additionalComponents, setAdditionalComponents] = useState([]);
  const [selectedFileType, setSelectedFileType] = useState('pem');

  const handleInputChange = (e) => {
    const { name, value, files } = e.target;
    if (files) {
      setFormData(prev => ({ ...prev, [name]: files[0] }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleFileTypeChange = (type) => {
    setSelectedFileType(type);
    setFormData(prev => ({ ...prev, pemFile: null, ppkFile: null }));
  };

  const addComponent = () => {
    const newComponent = {
      id: Date.now(),
      type: 'custom',
      label: 'Custom Component',
      value: '',
    };
    setAdditionalComponents([...additionalComponents, newComponent]);
  };

  const removeComponent = (id) => {
    setAdditionalComponents(additionalComponents.filter(comp => comp.id !== id));
  };

  const updateComponent = (id, field, value) => {
    setAdditionalComponents(additionalComponents.map(comp => 
      comp.id === id ? { ...comp, [field]: value } : comp
    ));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Profile Data:', { ...formData, additionalComponents });
    // Here you would typically send data to your backend
    alert('Profile setup completed!');
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
            Configure your server details and add custom components for your orchestration setup
          </p>
        </div>

        {/* Main Form */}
        <div className="bg-base-100 rounded-2xl shadow-xl border border-base-300 p-8">
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Basic Information */}
              <div className="space-y-6">
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
                    value={formData.name}
                    onChange={handleInputChange}
                    className="input input-bordered w-full bg-base-200 border-base-300 focus:border-primary"
                    placeholder="Enter your full name"
                    required
                  />
                </div>

                <div className="form-control">
                  <label className="label">
                    <span className="label-text text-base-content font-medium">Server Tag</span>
                    <span className="label-text-alt text-base-content/60">Used for identification</span>
                  </label>
                  <input
                    type="text"
                    name="serverTag"
                    value={formData.serverTag}
                    onChange={handleInputChange}
                    className="input input-bordered w-full bg-base-200 border-base-300 focus:border-primary"
                    placeholder="e.g., Production-Server-01"
                    required
                  />
                </div>
              </div>

              {/* Server Configuration */}
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-base-content mb-6 flex items-center gap-2">
                  <Server className="w-6 h-6" />
                  Server Configuration
                </h2>

                <div className="form-control">
                  <label className="label">
                    <span className="label-text text-base-content font-medium">IP Address</span>
                  </label>
                  <input
                    type="text"
                    name="ipAddress"
                    value={formData.ipAddress}
                    onChange={handleInputChange}
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
                    value={formData.hostname}
                    onChange={handleInputChange}
                    className="input input-bordered w-full bg-base-200 border-base-300 focus:border-primary"
                    placeholder="e.g., server01.example.com"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Security Configuration */}
            <div className="mt-12 pt-8 border-t border-base-300">
              <h2 className="text-2xl font-bold text-base-content mb-6 flex items-center gap-2">
                <Key className="w-6 h-6" />
                Security Configuration
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* File Upload Section */}
                <div className="space-y-4">
                  <div className="flex gap-4 mb-4">
                    <button
                      type="button"
                      onClick={() => handleFileTypeChange('pem')}
                      className={`btn ${selectedFileType === 'pem' ? 'btn-primary' : 'btn-outline'}`}
                    >
                      PEM File
                    </button>
                    <button
                      type="button"
                      onClick={() => handleFileTypeChange('ppk')}
                      className={`btn ${selectedFileType === 'ppk' ? 'btn-primary' : 'btn-outline'}`}
                    >
                      PPK File
                    </button>
                  </div>

                  <div className="form-control">
                    <label className="label">
                      <span className="label-text text-base-content font-medium">
                        {selectedFileType === 'pem' ? 'PEM Key File' : 'PPK Key File'}
                      </span>
                    </label>
                    <input
                      type="file"
                      name={selectedFileType === 'pem' ? 'pemFile' : 'ppkFile'}
                      onChange={handleInputChange}
                      className="file-input file-input-bordered w-full bg-base-200 border-base-300"
                      accept={selectedFileType === 'pem' ? '.pem' : '.ppk'}
                    />
                    {formData[selectedFileType === 'pem' ? 'pemFile' : 'ppkFile'] && (
                      <p className="mt-2 text-sm text-success">
                        ✓ File selected: {formData[selectedFileType === 'pem' ? 'pemFile' : 'ppkFile'].name}
                      </p>
                    )}
                  </div>
                </div>

                {/* Password Section */}
                <div className="form-control">
                  <label className="label">
                    <span className="label-text text-base-content font-medium">Server Password</span>
                    <span className="label-text-alt text-base-content/60">Optional if using key file</span>
                  </label>
                  <input
                    type="password"
                    name="serverPassword"
                    value={formData.serverPassword}
                    onChange={handleInputChange}
                    className="input input-bordered w-full bg-base-200 border-base-300 focus:border-primary"
                    placeholder="Enter server password"
                  />
                </div>
              </div>
            </div>

            {/* Additional Components */}
            <div className="mt-12 pt-8 border-t border-base-300">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-base-content flex items-center gap-2">
                  <Globe className="w-6 h-6" />
                  Additional Components
                </h2>
                <button
                  type="button"
                  onClick={addComponent}
                  className="btn btn-primary gap-2"
                >
                  <Plus className="w-5 h-5" />
                  Add Component
                </button>
              </div>

              {additionalComponents.length === 0 ? (
                <div className="text-center py-8 border-2 border-dashed border-base-300 rounded-lg">
                  <Globe className="w-12 h-12 text-base-content/30 mx-auto mb-4" />
                  <p className="text-base-content/60">No additional components added yet</p>
                  <p className="text-sm text-base-content/40 mt-2">
                    Click "Add Component" to add custom fields for your setup
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {additionalComponents.map((component) => (
                    <div key={component.id} className="flex gap-4 items-center p-4 bg-base-200 rounded-lg">
                      <div className="flex-1">
                        <input
                          type="text"
                          value={component.label}
                          onChange={(e) => updateComponent(component.id, 'label', e.target.value)}
                          className="input input-bordered w-full bg-base-100 mb-2"
                          placeholder="Component Label"
                        />
                        <input
                          type="text"
                          value={component.value}
                          onChange={(e) => updateComponent(component.id, 'value', e.target.value)}
                          className="input input-bordered w-full bg-base-100"
                          placeholder="Component Value"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => removeComponent(component.id)}
                        className="btn btn-error btn-square btn-sm"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
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
      </div>
    </div>
  );
};

export default ProfileSetup;
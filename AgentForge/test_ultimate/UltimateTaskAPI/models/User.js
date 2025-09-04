// models/User.js
export class Models/User {
  constructor() {
    this.initialized = false;
    this.data = [];
  }

  async initialize() {
    try {
      this.initialized = true;
      console.log('models/User.js initialized');
    } catch (error) {
      console.error('Initialization error:', error);
    }
  }

  async getData() {
    return this.data;
  }

  async setData(newData) {
    this.data = newData;
    return this.data;
  }

  async save() {
    console.log('Saving data...', this.data);
    return true;
  }
}

export default Models/User;

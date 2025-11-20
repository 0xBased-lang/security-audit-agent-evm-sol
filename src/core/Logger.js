/**
 * Logger - Consistent logging across the framework
 */

const chalk = require('chalk');

class Logger {
    constructor(verbosity = 'normal') {
        this.verbosity = verbosity; // 'silent', 'normal', 'verbose'
    }

    info(message) {
        if (this.verbosity === 'silent') return;
        console.log(chalk.blue('ℹ'), message);
    }

    success(message) {
        if (this.verbosity === 'silent') return;
        console.log(chalk.green('✓'), message);
    }

    warn(message) {
        if (this.verbosity === 'silent') return;
        console.log(chalk.yellow('⚠'), message);
    }

    error(message) {
        console.error(chalk.red('✖'), message);
    }

    verbose(message) {
        if (this.verbosity !== 'verbose') return;
        console.log(chalk.gray('→'), message);
    }

    section(title) {
        if (this.verbosity === 'silent') return;
        console.log('\n' + chalk.bold.cyan('═══ ' + title + ' ═══') + '\n');
    }
}

module.exports = Logger;

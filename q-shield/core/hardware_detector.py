import platform
import os
import cpuinfo
from typing import Dict, Any, List

class HardwareCapabilities:
    """Detect hardware cryptographic capabilities"""
    
    def __init__(self):
        self.cpu_info = cpuinfo.get_cpu_info()
        self.platform_info = platform.platform()
        self.capabilities = self._detect_capabilities()
        self.memory_info = self._get_memory_info()
        self.arch_info = self._get_architecture_info()
    
    def _detect_capabilities(self) -> Dict[str, bool]:
        """Detect available hardware features"""
        caps = {
            'aes_ni': False,
            'avx2': False,
            'avx512': False,
            'neon': False,
            'crypto_extension': False,
            'secure_element': False,
            'has_crypto_acceleration': False,
            'rdrand': False,
            'rdseed': False
        }
        
        flags = self.cpu_info.get('flags', [])
        
        # Check for AES-NI support
        if 'aes' in flags:
            caps['aes_ni'] = True
            caps['has_crypto_acceleration'] = True
        
        # Check for AVX2 support
        if 'avx2' in flags:
            caps['avx2'] = True
        
        # Check for AVX-512 support
        if any(flag.startswith('avx512') for flag in flags):
            caps['avx512'] = True
        
        # Check for ARM NEON support
        if 'neon' in flags or 'asimd' in flags:
            caps['neon'] = True
            caps['has_crypto_acceleration'] = True
        
        # Check for ARM crypto extensions
        if any(flag in flags for flag in ['aes', 'sha1', 'sha2', 'crypto']):
            caps['crypto_extension'] = True
            caps['has_crypto_acceleration'] = True
        
        # Check for hardware random number generators
        if 'rdrand' in flags:
            caps['rdrand'] = True
        
        if 'rdseed' in flags:
            caps['rdseed'] = True
        
        # Check for secure element (basic check for TPM/TEE)
        if os.path.exists('/dev/tpm0') or os.path.exists('/dev/tpmrm0'):
            caps['secure_element'] = True
        
        # Check for ARM TrustZone
        if os.path.exists('/sys/bus/tee'):
            caps['secure_element'] = True
        
        return caps
    
    def _get_memory_info(self) -> Dict[str, int]:
        """Get system memory information"""
        memory_info = {
            'total_ram': 0,
            'available_ram': 0,
            'total_flash': 0,
            'available_flash': 0
        }
        
        try:
            # Linux/Unix memory detection
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                for line in meminfo.split('\n'):
                    if 'MemTotal' in line:
                        memory_info['total_ram'] = int(line.split()[1])  # KB
                    elif 'MemAvailable' in line:
                        memory_info['available_ram'] = int(line.split()[1])  # KB
        except:
            # Fallback for non-Linux systems
            try:
                import psutil
                mem = psutil.virtual_memory()
                memory_info['total_ram'] = mem.total // 1024  # Convert to KB
                memory_info['available_ram'] = mem.available // 1024  # Convert to KB
            except ImportError:
                # Default values if psutil not available
                memory_info['total_ram'] = 1024 * 1024  # 1GB default
                memory_info['available_ram'] = 512 * 1024  # 512MB default
        
        return memory_info
    
    def _get_architecture_info(self) -> Dict[str, str]:
        """Get CPU architecture information"""
        return {
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture()[0],
            'cpu_brand': self.cpu_info.get('brand_raw', 'Unknown')
        }
    
    def has_sufficient_memory(self, min_ram_kb: int = 16384) -> bool:
        """Check if device has sufficient memory for PQC operations"""
        return self.memory_info['total_ram'] > min_ram_kb
    
    def get_optimal_algorithms(self) -> Dict[str, str]:
        """Return optimal algorithms based on hardware"""
        if self.capabilities['has_crypto_acceleration']:
            return {
                'symmetric': 'aes_gcm',
                'kyber_variant': 'kyber512',
                'dilithium_variant': 'dilithium2',
                'hash': 'sha256'
            }
        else:
            return {
                'symmetric': 'chacha20_poly1305',
                'kyber_variant': 'kyber512_compact',
                'dilithium_variant': 'dilithium2_compact',
                'hash': 'blake3'
            }
    
    def get_performance_profile(self) -> str:
        """Determine device performance profile"""
        ram_mb = self.memory_info['total_ram'] // 1024
        
        if (self.capabilities['has_crypto_acceleration'] and 
            ram_mb >= 512):
            return "high_performance"
        elif ram_mb >= 64:
            return "standard"
        else:
            return "constrained"
    
    def get_random_source(self) -> str:
        """Get best available random number source"""
        if self.capabilities['rdseed']:
            return 'rdseed'
        elif self.capabilities['rdrand']:
            return 'rdrand'
        elif os.path.exists('/dev/urandom'):
            return 'urandom'
        else:
            return 'software'
    
    def supports_pqc(self) -> bool:
        """Check if hardware can support PQC operations"""
        min_ram_for_pqc = 32 * 1024  # 32MB minimum
        return self.has_sufficient_memory(min_ram_for_pqc)
    
    def get_capability_summary(self) -> Dict[str, Any]:
        """Get comprehensive hardware capability summary"""
        return {
            'profile': self.get_performance_profile(),
            'crypto_acceleration': self.capabilities['has_crypto_acceleration'],
            'memory_mb': self.memory_info['total_ram'] // 1024,
            'architecture': self.arch_info['machine'],
            'optimal_algorithms': self.get_optimal_algorithms(),
            'random_source': self.get_random_source(),
            'pqc_capable': self.supports_pqc(),
            'secure_element': self.capabilities['secure_element']
        }

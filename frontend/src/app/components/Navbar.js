import Image from 'next/image';
import Link from 'next/link';

const Navbar = () => {

    return (
        <>
            {/* NAVBAR */}
            < div className='fixed z-50 top-0 bg-white border-b border-secondary flex items-center gap-10 w-full justify-start px-16 h-20' >
                <div className=' text-primary w-full text-xl font-bold flex justify-start items-center gap-3'>
                    <Image src={'/logo.svg'} width={125} height={125} alt="LOGO" />
                </div>

                <div className=' text-black w-40 border-b border-white hover:border-primary transition-all'>
                    <Link href={'/'} >URL CHECKER</Link>
                </div>
                <div className=' text-black w-32 border-b border-white hover:border-primary transition-all'>
                    <Link href={'/cases'} >CASES-LIST</Link>
                </div>
            </div >

        </>
    )
}

export default Navbar;
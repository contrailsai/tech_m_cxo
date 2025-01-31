import Link from "next/link"
const Footer = () => {
    return (
        <>
            {/* FOOTER */}
            <div className=' bg-white flex gap-3 py-2 justify-center items-center border-t border-primary '>
                <Link href={'https://contrails.ai'} target='_blank' className='hover:underline'>
                    Contrails AI
                </Link>
                ©2024
            </div>
        </>
    )
}

export default Footer;